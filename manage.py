import click

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
    from flask_mongoengine import DoesNotExist
    from cdr.api.models import ClinicalDoc, Observation, Status

    legit_doc_references, legit_status_references = set(), set()
    obs_purge_count, status_purge_count = 0, 0

    # 'pk' (primary key) is the internal name for '_id'
    for doc in ClinicalDoc.objects.only('pk'):
        legit_doc_references.add(doc.pk)

    print("{} legit doc references found".format(len(legit_doc_references)))

    for obs in Observation.objects.only('pk', 'owner', 'status'):
        purge_pk = None
        try:
            if obs.owner.pk not in legit_doc_references:
                purge_pk = obs.pk
            else:
                legit_status_references.add(obs.status.pk)
        except DoesNotExist:
            purge_pk = obs.pk

        if purge_pk is not None:
            obs_purge_count += 1
            if not preview:
                obs.delete()

    for stat in Status.objects.only('pk'):
        if stat.pk not in legit_status_references:
            status_purge_count += 1
            if not preview:
                stat.delete()

    if preview:
        print("PREVIEW OF OPERATIONS:")
    print("Deleted {} observations".format(obs_purge_count))
    print("Deleted {} status objects".format(status_purge_count))
