"""Migrate latest mongo content into postgres

Revision ID: d4e24d532aaa
Revises: 
Create Date: 2019-11-20 09:53:58.970000

"""
import logging
from mongoengine.errors import DoesNotExist
import time

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
revision = 'd4e24d532aaa'
down_revision = 'd4e24d532ae4'
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
        except DoesNotExist as dne:
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
        except DoesNotExist as dne:
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

    mongo_obs = ObservationMDB.objects(owner=mongo_doc)
    for mongo_ob in mongo_obs:
        ob = Observation(doc_id=doc.mrn)
        ob.code_id = code_from_mongo(mongo_ob, "code")
        ob.icd9_id = code_from_mongo(mongo_ob, "icd9")
        ob.icd10_id = code_from_mongo(mongo_ob, "icd10")
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
    report_progress("  and {} docs in Mongo".format(mongo_docs.count()))

    # nothing changes historically, just migrate the ones received since
    # the last migration ran - backdate a bit just to be safe
    last_receipt_time = parse_datetime("2019-11-15 00:00:00")
    log.warning("last receipt time: {}".format(last_receipt_time))

    mongo_docs = ClinicalDocMDB.objects(receipt_time__gte=last_receipt_time)
    total = mongo_docs.count()
    log.debug("{} newish Mongo records found".format(total))

    progress = 0
    batch_size = 10
    for mongo_doc in mongo_docs:
        migrate_doc(mongo_doc)
        progress += 1
        if progress % batch_size == 0:
            report_progress(" {0} docs of {1} migrated, {2:.1f}%".format(progress, total, progress/total*100))
            sdb.session.commit()

    log.debug("Final count, {} docs in PG".format(ClinicalDoc.query.count()))
    sdb.session.commit()


def downgrade():
    # no downgrade path - create fresh postgres database if necessary
    pass