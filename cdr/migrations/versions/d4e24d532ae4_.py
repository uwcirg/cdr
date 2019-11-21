"""Migrate mongo content into postgres

NB - Mongo has since been removed from the project - references within
commented out with prefix '#MongoNoMore' to prevent build errors

Revision ID: d4e24d532ae4
Revises: 
Create Date: 2019-08-28 09:53:58.970000

"""
import logging
#MongoNoMore from mongoengine.errors import DoesNotExist
import time

from cdr.extensions import sdb
from cdr.api.models import (
    ClinicalDoc,
    Code,
    Observation,
    Status,
)
#MongoNoMore from cdr.api.mongo_models import (
#MongoNoMore     ClinicalDoc as ClinicalDocMDB,
#MongoNoMore     Observation as ObservationMDB,
#MongoNoMore )
from cdr.time_util import parse_datetime

# revision identifiers, used by Alembic.
revision = 'd4e24d532ae4'
down_revision = None
branch_labels = None
depends_on = None

log = logging.getLogger('alembic.runtime.migration')
log.setLevel(logging.DEBUG)
last_report_time = 0


def report_progress(message):
    """suppress progress messages if 30 seconds haven't passed

    cuts down on hoards of noise during startup phase
    """
    global last_report_time
    cur = time.time()
    if cur - last_report_time > 30:
        log.debug(message)
        last_report_time = cur


def migrate_doc(mongo_doc):
    def doc_exists(mongo_doc):
        existing = ClinicalDoc.query.get(mongo_doc.mrn)
        if existing and (
                existing.receipt_time >=
                parse_datetime(mongo_doc.receipt_time)):
            report_progress(
                "  skipping import on existing {}".format(existing.mrn))
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

    def code_from_mongo(obj, attr_name):
        try:
            mongo_code = getattr(obj, attr_name, None)
    #MongoNoMore         except DoesNotExist as dne:
        except Exception as dne:
            log.exception(dne)
            log.warning(
                "Code reference for {} missing in MongoDB".format(attr_name))
            return None
        if mongo_code is None:
            return None
        try:
            code = Code(
                code=mongo_code.code,
                code_system=mongo_code.code_system,
                code_system_name=mongo_code.code_system_name,
                display=mongo_code.display)
            return code.save().id
        # MongoNoMore         except DoesNotExist as dne:
        except Exception as dne:
            log.exception(dne)
            log.warning("Code reference missing in MongoDB")

    def status_from_mongo(mongo_status):
        if mongo_status is None:
            return None
        status = Status(
            status_code=mongo_status.status_code,
            code_id=code_from_mongo(mongo_status, "code"),
            value_id=code_from_mongo(mongo_status, "value"))
        return status.save().id

    #MongoNoMore mongo_obs = ObservationMDB.objects(owner=mongo_doc)
    mongo_obs = []
    for mongo_ob in mongo_obs:
        ob = Observation(doc_id=doc.mrn)
        ob.code_id = code_from_mongo(mongo_ob, "code")
        ob.icd9_id = code_from_mongo(mongo_ob, "icd9")
        ob.icd10_id = code_from_mongo(mongo_ob, "icd10")
        ob.entry_date = mongo_ob.entry_date
        ob.onset_date = mongo_ob.onset_date
        try:
            ob.status_id = status_from_mongo(mongo_ob.status)
        # MongoNoMore         except DoesNotExist as dne:
        except Exception as dne:
            log.exception(dne)
            log.warning(
                "Status reference missing in MongoDB for"
                " document {)".format(doc.mrn))
        sdb.session.add(ob)


def upgrade():
    initial_pg_count = ClinicalDoc.query.count()
    log.debug("Initiate with {} docs in PG".format(initial_pg_count))
    #MongoNoMore mongo_docs = ClinicalDocMDB.objects
    mongo_docs = []
    total = mongo_docs.count()
    report_progress("  and {} docs in Mongo".format(total))

    progress = 0
    batch_size = 10
    for mongo_doc in mongo_docs:
        migrate_doc(mongo_doc)
        progress += 1
        if progress % batch_size == 0:
            report_progress(" {} docs of {} migrated".format(progress, total))
            sdb.session.commit()

    log.debug("Final count, {} docs in PG".format(ClinicalDoc.query.count()))
    sdb.session.commit()


def downgrade():
    # no downgrade path - create fresh postgres database if necessary
    pass
