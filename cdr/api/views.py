from flask import abort, Blueprint, current_app, request, jsonify
from flask.ext.mongoengine import DoesNotExist

from ..extensions import db
from .models import ClinicalDoc, Unparsed

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/ccda/<string:mrn>')
def api_index(mrn):
    unparsed = Unparsed.objects.get_or_404(mrn=mrn)
    try:
        parsed = ClinicalDoc.objects.get(mrn=mrn)
    except DoesNotExist:
        parsed = None
    return jsonify(mrn=mrn, filepath=unparsed['filepath'])


@api.route('/ccda/<string:mrn>', methods=('PUT',))
def upload_ccda(mrn):
    data = request.json
    unparsed = Unparsed(mrn=mrn, filepath=data['filepath'])
    unparsed.save()
    return jsonify(message='upload ok')
