from __future__ import absolute_import, unicode_literals
from celery import shared_task

from django.db.utils import OperationalError, ProgrammingError
from django.utils.timezone import now


@shared_task
def submit_query(job_id):
    from daiquiri_core.adapter import get_adapter
    from daiquiri_query.models import QueryJob
    from daiquiri_uws.settings import PHASE_EXECUTING, PHASE_COMPLETED, PHASE_ERROR, PHASE_ABORTED

    # get the job object from the database
    job = QueryJob.objects.get(pk=job_id)

    # get the adapter with the database specific functions
    adapter = get_adapter('data')

    # set database and start time
    job.start_time = now()

    job.pid = adapter.fetch_pid()
    job.actual_query = adapter.build_query(job.database_name, job.table_name, job.actual_query)
    job.phase = PHASE_EXECUTING
    job.start_time = now()
    job.save()

    # get the actual query and submit the job to the database
    try:
        # this is where the work ist done (and the time is spend)
        adapter.execute(job.actual_query)

    except ProgrammingError as e:
        job.phase = PHASE_ERROR
        job.metadata = {
            'errors': str(e)
        }

    except OperationalError as e:
        # load the job again and check if the job was killed
        job = QueryJob.objects.get(pk=job_id)

        if job.phase != PHASE_ABORTED:
            job.phase = PHASE_ERROR
            job.metadata = {
                'errors': str(e)
            }
    else:
        # get additional information about the completed job
        job.phase = PHASE_COMPLETED

    finally:
        # get timing and save the job object
        job.end_time = now()
        job.execution_duration = (job.end_time - job.start_time).seconds

        # get additional information about the completed job
        if job.phase == PHASE_COMPLETED:
            job.nrows, job.size = adapter.fetch_stats(job.database_name, job.table_name)
            job.metadata = adapter.fetch_table(job.database_name, job.table_name)
            job.metadata['columns'] = adapter.fetch_columns(job.database_name, job.table_name)

        job.save()

    return job.phase
