import click
import sys
from time import sleep

from cdr import create_app


app = create_app()


@click.option(
    '--preview', '-p', default=False,
    help='Simply preview what to delete, do not execute')
@app.cli.command('remove-orphans')
def remove_orphans(preview):
    """Remove orphaned observation and status items

    The system maintains a single (most recent) ClinicalDoc for each
    known patient.  As a new ClinicalDoc may refer to a subset of the
    observations previously referenced, this leaves behind orphan
    observations that should be purged in the name of space.

    Furthermore, observations retain a status reference.  With observation
    updates, many stale status objects are left behind.

    Implemented as cli command for easy sysadmin calls.  The magnitude
    of the status collection exceeded mongo's `distinct` operation from
    working, thus the need to implement in code.

    :param preview: if set, only return the counts that would be purged,
      don't actually commit any change

    """
    from cdr.api.models import ClinicalDoc, Observation, Status

    legit_doc_references, legit_status_references = set(), set()
    status_purge_count = 0

    # 'pk' (primary key) is the internal name for '_id'
    for doc in ClinicalDoc.objects.only('pk'):
        legit_doc_references.add(doc.pk)

    print("{} legit doc references found".format(len(legit_doc_references)))

    # OOM problems require batching.  include occasional sleep for more
    # critical tasks
    batchsize = 10000
    done = 0
    worklist = Observation.objects.count()
    for i in range(0, worklist, batchsize):
        for obs in Observation.objects.only('status')[i:i+batchsize]:
            legit_status_references.add(obs.status.pk)
            done += 1

        print("{} of {} obs reviewed; {} legit status refs thus far".format(
            done, worklist, len(legit_status_references)))
        sys.stdout.flush()
        sleep(1)

    done = 0
    worklist = Status.objects.count()
    print("Begin status purge: {} objects exist, {} are valid".format(
        worklist, len(legit_status_references)))
    sys.stdout.flush()
    for i in range(0, worklist, batchsize):
        for stat in Status.objects.only('pk')[i:i+batchsize]:
            if stat.pk not in legit_status_references:
                status_purge_count += 1
                if not preview:
                    stat.delete()
            done += 1
        print("{} of {} stati reviewed; {} status objs purged".format(
            done, worklist, status_purge_count))
        sys.stdout.flush()
        sleep(1)

    if preview:
        print("PREVIEW OF OPERATIONS:")
    print("Deleted {} status objects".format(status_purge_count))
