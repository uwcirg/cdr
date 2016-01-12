from flask import abort, Blueprint, current_app, request, jsonify
from flask.ext.mongoengine import DoesNotExist
import json
import os
import urllib

from ..extensions import db
from ..time_util import isoformat_w_tz, parse_datetime
from .models import ClinicalDoc, parse_problem_list
from .models import Observation

api = Blueprint('api', __name__, url_prefix='')

@api.route('/test')
def hello():
    return jsonify(hi='there')


@api.route('/patients/<string:mrn>/ccda/file_info')
def api_index(mrn):
    doc = ClinicalDoc.objects.get_or_404(mrn=mrn)
    return jsonify(mrn=mrn, filepath=doc['filepath'],
                   receipt_time=isoformat_w_tz(doc['receipt_time']))


def filter_func(filter_parameters):
    """Generator, returns a function based on value of filter_parameters

    Filter paratmeters expected to be url-encoded JSON string (if
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
                           return status_match(require_status,
                                               observation['status'])
                       else:
                           return True
       # Never matched, filter out
       return False

    return filter_observation


@api.route('/patients/<string:mrn>/problem_list')
def get_problem_list(mrn):
    doc = ClinicalDoc.objects.get_or_404(mrn=mrn)
    problem_list = []
    observations = Observation.objects(owner=doc)

    pass_filter = filter_func(request.args.get("filter"))

    for obs in observations:
        problem = {}
        for e in ('code', 'icd9', 'icd10', 'onset_date', 'entry_date',
                  'status'):
            if e in obs:
                if hasattr(obs[e], 'isoformat'):
                    problem[e] = isoformat_w_tz(obs[e])
                else:
                    problem[e] = obs[e].to_json()
        if pass_filter(problem):
            problem_list.append(problem)

    return jsonify(mrn=mrn, receipt_time=isoformat_w_tz(doc['receipt_time']),
                  problem_list=problem_list)


def archiveCCDA(filepath, mrn):
    """Move the given file to the appropriate archive directory"""
    mrn = str(mrn)
    bucket = mrn[-3:]
    source_d = os.path.dirname(filepath)
    archive = os.path.join(source_d, 'archive')
    if not os.path.exists(archive):
        os.mkdir(archive)
    dest_d = os.path.join(archive, bucket)
    if not os.path.exists(dest_d):
        os.mkdir(dest_d)
    dest = os.path.join(dest_d, mrn)
    if os.path.exists(dest):
        os.remove(dest)
    os.rename(filepath, dest)
    return dest


@api.route('/patients/<string:mrn>/ccda', methods=('PUT',))
def upload_ccda(mrn):
    data = request.json
    # Check for existing record for this MRN
    try:
        doc = ClinicalDoc.objects.get(mrn=mrn)
        replace = True
    except DoesNotExist:
        doc = None
        replace = False

    if doc and datetime_w_tz(doc.generation_time) >=\
            parse_datetime(data['effectiveTime']):
        current_app.logger.info("found better data for MRN {} already"
                                " present".format(mrn))
        os.remove(data['filepath'])
        return jsonify(message='obsolete')

    filepath = archiveCCDA(data['filepath'], mrn)
    if not replace:
        doc = ClinicalDoc(mrn=mrn, filepath=filepath)

    if 'effectiveTime' in data:
        doc.generation_time = parse_datetime(data['effectiveTime'])
    if 'receipt_time' in data:
        doc.receipt_time = parse_datetime(data['receipt_time'])

    doc.save()
    parse_problem_list(data.get('problem_list'), clinical_doc=doc,
                       replace=replace)
    return jsonify(message='upload ok')
