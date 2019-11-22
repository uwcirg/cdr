from flask import abort, Blueprint, current_app, request, jsonify
import json
from os import getenv
from sqlalchemy.orm.exc import NoResultFound

from ..extensions import sdb
from ..time_util import datetime_w_tz, isoformat_w_tz, parse_datetime
from .models import ClinicalDoc, parse_problem_list
from .models import Code, Observation

PROXYPATH = getenv('PROXYPATH', '')
api = Blueprint('api', __name__, url_prefix=PROXYPATH)


@api.route('/test')
def hello():
    return jsonify(hi='there')


@api.route('/patients/<string:mrn>/ccda/file_info')
def api_index(mrn):
    doc = ClinicalDoc.query.get_or_404(mrn)
    return jsonify(
        mrn=mrn, filepath=doc.filepath,
        receipt_time=isoformat_w_tz(doc.receipt_time))


@api.route('/codes/<system>')
def codes_by_system(system):
    """Presents a list of diagnosis for the requested system"""
    if system == 'icd9':
        system = 'ICD-9-CM'
    if system == 'icd10':
        system = 'ICD-10-CM'

    codes = Code.query.filter_by(code_system_name=system)
    data = []
    for code in codes:
        data.append(code.to_json())
    return jsonify(codes=data)


@api.route('/diagnosis/<system>/<code>/patients')
def patients_w_icd9code(system, code):
    """Presents a list of patients with the given icd9/10 code"""
    if system not in ('icd9', 'icd10'):
        abort(400, "unsupported system: {}".format(system))

    try:
        matching_code = Code.query.filter_by(code=code).one()
    except NoResultFound:
        abort(404)

    if system == 'icd9':
        observations = Observation.query.filter_by(icd9_id=matching_code.id)
    else:
        observations = Observation.query.filter_by(icd10_id=matching_code.id)
    data = dict()
    data['diagnosis'] = matching_code.to_json()
    for obs in observations:
        data[obs.doc_id] = obs.status.to_json()
    return jsonify(patients=data)


def filter_func(filter_parameters):
    """Generator, returns a function based on value of filter_parameters

    Filter parameters expected to be url-encoded JSON string (if
    defined)  It defines the list of parameters to search on.

    """

    def field_match(subfield, patterns, contents):
        """Returns true if contents match field_rule parameters"""
        if subfield not in contents:
            return False

        for pattern in patterns:
            if pattern.endswith('*'):
                if contents[subfield].startswith(pattern[:-1]):
                    return True
            elif contents[subfield] == pattern:
                return True
        return False

    def status_match(status_rule, contents):
        for key in status_rule:
            match_dict = status_rule[key]
            for field in match_dict:
                if match_dict[field] != contents[key][field]:
                    return False
        return True

    if not filter_parameters:
        """Without filter parameters, everything passes the filter """
        return lambda x: True

    params = json.loads(filter_parameters)
    filter_by = params['filter']
    require_status = params.get('status')

    def filter_observation(observation):
        """All params treated as 'or' - return true as soon as one hits"""
        for field in filter_by:
            if field in observation:
                for subfield, patterns in filter_by[field].items():
                    if field_match(subfield, patterns, observation[field]):
                        # Found a matching field, confirm status if required
                        if require_status:
                            return status_match(
                                require_status, observation['status'])
                        else:
                            return True
        # Never matched, filter out
        return False

    return filter_observation


@api.route('/patients/<string:mrn>/problem_list')
def get_problem_list(mrn):
    doc = ClinicalDoc.query.get_or_404(mrn)
    problem_list = []
    observations = Observation.query.filter_by(doc_id=doc.mrn)

    pass_filter = filter_func(request.args.get("filter"))

    for obs in observations:
        problem = {}
        for e in (
                'code', 'icd9', 'icd10', 'onset_date', 'entry_date',
                'status'):
            if getattr(obs, e):
                if hasattr(getattr(obs, e), 'isoformat'):
                    problem[e] = isoformat_w_tz(getattr(obs, e))
                else:
                    problem[e] = getattr(obs, e).to_json()
        if pass_filter(problem):
            problem_list.append(problem)

    return jsonify(
        mrn=mrn, receipt_time=isoformat_w_tz(doc.receipt_time),
        problem_list=problem_list)


@api.route('/patients/<string:mrn>/ccda', methods=('PUT',))
def upload_ccda(mrn):
    """Persist the CCDA for given MRN unless a newer one exists"""
    data = request.json
    # with open('/tmp/save-{}'.format(mrn), 'w') as backup:
    #     backup.write(json.dumps(data['problem_list'], indent=2))

    # Check for existing record for this MRN
    replace = False
    doc = ClinicalDoc.query.get(mrn)
    if doc:
        replace = True

    if doc and datetime_w_tz(doc.generation_time) >=\
            parse_datetime(data['effectiveTime']):
        current_app.logger.info("found better data for MRN {} already"
                                " present".format(mrn))
        return jsonify(message='obsolete')

    filepath = data['filepath']
    if doc is None:
        doc = ClinicalDoc(mrn=mrn, filepath=filepath)

    if 'effectiveTime' in data:
        doc.generation_time = parse_datetime(data['effectiveTime'])
    if 'receipt_time' in data:
        doc.receipt_time = parse_datetime(data['receipt_time'])

    doc.save()
    parse_problem_list(
        data.get('problem_list'), clinical_doc=doc, replace=replace)
    sdb.session.commit()
    return jsonify(message='upload ok')
