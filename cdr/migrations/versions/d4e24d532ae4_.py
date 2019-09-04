"""Migrate mongo content into postgres

Revision ID: d4e24d532ae4
Revises: 
Create Date: 2019-08-28 09:53:58.970000

"""
import logging
from mongoengine.errors import DoesNotExist

from cdr.extensions import sdb
from cdr.api.models import (
    ClinicalDoc,
    Code,
    Observation,
    Status,
)
from cdr.api.mongo_models import (
    ClinicalDoc as ClinicalDocMDB,
    Observation as ObservationMDB,
)
from cdr.time_util import parse_datetime

# revision identifiers, used by Alembic.
revision = 'd4e24d532ae4'
down_revision = None
branch_labels = None
depends_on = None

log = logging.getLogger('alembic.runtime.migration')
log.setLevel(logging.DEBUG)


def migrate_doc(mongo_doc):
    def doc_exists(mongo_doc):
        existing = ClinicalDoc.query.get(mongo_doc.mrn)
        if existing and (
                existing.receipt_time >=
                parse_datetime(mongo_doc.receipt_time)):
            log.debug("  skipping import on existing {}".format(existing.mrn))
            return True

    if doc_exists(mongo_doc):
        return

    doc = ClinicalDoc(
        mrn=mongo_doc.mrn,
        filepath=mongo_doc.filepath
    )
    doc.generation_time = mongo_doc.generation_time
    doc.receipt_time = mongo_doc.receipt_time
    doc.lastvisit_time = mongo_doc.lastvisit_time
    doc.save()

    def code_from_mongo(mongo_code):
        if mongo_code is None:
            return None
        code = Code(
            code=mongo_code.code,
            code_system=mongo_code.code_system,
            code_system_name=mongo_code.code_system_name,
            display=mongo_code.display)
        return code.save().id

    def status_from_mongo(mongo_status):
        if mongo_status is None:
            return None
        status = Status(
            status_code=mongo_status.status_code,
            code_id=code_from_mongo(mongo_status.code),
            value_id=code_from_mongo(mongo_status.value))
        return status.save().id

    mongo_obs = ObservationMDB.objects(owner=mongo_doc)
    for mongo_ob in mongo_obs:
        ob = Observation(doc_id=doc.mrn)
        ob.code_id = code_from_mongo(mongo_ob.code)
        ob.icd9_id = code_from_mongo(mongo_ob.icd9)
        ob.icd10_id = code_from_mongo(mongo_ob.icd10)
        ob.entry_date = mongo_ob.entry_date
        ob.onset_date = mongo_ob.onset_date
        try:
            ob.status_id = status_from_mongo(mongo_ob.status)
        except DoesNotExist as dne:
            log.exception(dne)
            log.warning(
                "Status reference missing in MongoDB for"
                " document {)".format(doc.mrn))
        sdb.session.add(ob)


def upgrade():
    initial_pg_count = ClinicalDoc.query.count()
    log.debug("Initiate with {} docs in PG".format(initial_pg_count))
    mongo_docs = ClinicalDocMDB.objects
    total = mongo_docs.count()
    log.debug("  and {} docs in Mongo".format(total))

    progress = 0
    batch_size = 10
    for mongo_doc in mongo_docs:
        migrate_doc(mongo_doc)
        progress += 1
        if progress % batch_size == 0:
            log.debug(" {} docs of {} migrated".format(progress, total))
            sdb.session.commit()

    log.debug("Final count, {final_pg_count} docs in PG".format(
        ClinicalDoc.query.count()))
    sdb.session.commit()


def downgrade():
    # no downgrade path - create fresh postgres database if necessary
    pass
