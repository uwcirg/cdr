from flask import abort, Blueprint, current_app, request, jsonify
from flask.ext.mongoengine import DoesNotExist
import json
import os

from ..extensions import db
from .models import ClinicalDoc, parse_problem_list, parse_datetime
from .models import Observation

api = Blueprint('api', __name__, url_prefix='')

@api.route('/test')
def hello():
    return jsonify(hi='there')


import pytz

def isoformat_w_tz(dt):
    """Mongo stores all datetime objects in UTC, add the TZ back on"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    return dt.isoformat()


@api.route('/patients/<string:mrn>/ccda/file_info')
def api_index(mrn):
    doc = ClinicalDoc.objects.get_or_404(mrn=mrn)
    return jsonify(mrn=mrn, filepath=doc['filepath'],
                   receipt_time=isoformat_w_tz(doc['receipt_time']))


@api.route('/patients/<string:mrn>/problem_list')
def get_problem_list(mrn):
    doc = ClinicalDoc.objects.get_or_404(mrn=mrn)
    problem_list = []
    observations = Observation.objects(owner=doc)
    for obs in observations:
        problem = {}
        for e in ('code', 'icd9', 'icd10', 'onset_date', 'entry_date',
                  'status'):
            if e in obs:
                if hasattr(obs[e], 'isoformat'):
                    problem[e] = isoformat_w_tz(obs[e])
                else:
                    problem[e] = obs[e].to_json()
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

    if doc and doc.generation_time > data['effectiveTime']:
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
