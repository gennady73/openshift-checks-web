import asyncio
import json
import os
import time
import urllib.request
from flask import Blueprint, render_template, url_for, request, redirect, flash
from flask import Flask
from flask_apscheduler import APScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_JOB_MODIFIED, EVENT_JOB_SUBMITTED
import logging
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import ConflictingIdError, JobLookupError

from jobstores.sqlalchemy import SQLAlchemyJobStore
from models.job_log import JobLog

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

app:Flask = None

scheduler_blueprint: Blueprint = Blueprint('scheduler', __name__, template_folder='templates/schedule')
scheduler = APScheduler()
scheduler_global_state = dict({
    "paused": False,
    "jobstore": "",
    'max_log_entries': 10,
    "log": {}
})


@scheduler_blueprint.route('/', methods=['GET', 'POST'])
def scheduler_home():
    # The logic for the scheduler home page

    # Fetch basic information about the webapp from the API endpoint
    jobs_api_url = f'{request.host_url}scheduler'
    response = urllib.request.urlopen(jobs_api_url)
    data = response.read()

    if response.code == 200:
        # Parse the JSON response
        scheduler_state = json.loads(data)

    scheduler_state['paused'] = scheduler_global_state['paused']
    jobs = scheduler_get_jobs_data()
    return render_template('list.html', scheduler_state=scheduler_state, active_tab="Scheduler",
                           jobs=jobs,
                           active_tab2="JobList",
                           cluster_info_list=app.cluster_info_list,
                           clusters=app.clusters)


@scheduler_blueprint.route('/action', methods=['GET', 'POST'])
def scheduler_action():

    #if request.method == 'POST':
    action_param = request.args.get('action_id')
    if action_param == "scheduler_stop":
        scheduler_api_url = f'{request.host_url}scheduler/pause'
        response = requests.post(scheduler_api_url)
        if response.status_code == 200 or response.status_code == 204:
            data = response.content
            scheduler_global_state['paused'] = True
            logging.getLogger('apscheduler').info(f"The scheduler is paused.")
        else:
            logging.getLogger('apscheduler').error(f"Failed to stop scheduler!")
    elif action_param == "scheduler_start":
        scheduler_api_url = f'{request.host_url}scheduler/resume'
        response = requests.post(scheduler_api_url)
        if response.status_code == 200 or response.status_code == 204:
            data = response.content
            scheduler_global_state['paused'] = False
            logging.getLogger('apscheduler').info(f"The scheduler is resumed.")
        else:
            logging.getLogger('apscheduler').error(f"Failed to start scheduler!")
            logging.getLogger('apscheduler').debug(
                f"Failed to start scheduler! Response: {response.content if response.content else 'no response content.'}")
    else:
        logging.getLogger('apscheduler').error(f"Invalid parameter: {action_param}")

    return redirect(url_for('scheduler.scheduler_home'))


@scheduler_blueprint.route('/job/<job_id>')
def scheduler_job(job_id):
    # Add your logic for the individual job page
    if job_id is None or job_id == "":
        raise Exception(f"The job_id is not valid: '{job_id}'.")

    # global scheduler_global_state
    # scheduler_global_state = update_scheduler_global_state(global_state=scheduler_global_state,
    #                                                      jobstore=scheduler_global_state["jobstore"], job_id=job_id)


    # if job_id not in scheduler_global_state["log"]:
    #     scheduler_global_state['log'][job_id] = {"runs": 0, "fails": 0, "events": []}

    jobstore = scheduler_global_state["jobstore"]
    job = scheduler.scheduler.get_job(job_id, jobstore)
    # job_fails = scheduler_global_state["log"].get(job_id)["fails"]
    # job_runs = scheduler_global_state["log"].get(job_id)["runs"] + job_fails
    # log = scheduler_global_state["log"].get(job_id)["events"]
    max_log_entries = scheduler_global_state["max_log_entries"]

    job_global_state = get_scheduler_global_state(job_id)
    if len(job_global_state) > 0:
        job_fails = job_global_state["fails"]
        job_runs = job_global_state["runs"] + job_fails
        log = job_global_state["events"]
    else:
        job_fails = 0
        job_runs = 0
        log = []

    try:
        job_logs = app.logs.get_all_jobs_by_id(job_id=job_id)
        for job_log in job_logs:
            logging.getLogger('apscheduler').debug(f"Get job log:{job_log}")

    except Exception as ex:
        logging.getLogger('apscheduler').error(f'Failed to get job log: {ex}')

    return render_template('job.html', job_id=job_id, job=job, jobstore=jobstore,
                           log=log, max_log_entries=max_log_entries, job_runs=f"{job_runs}", job_fails=f"{job_fails}")


@scheduler_blueprint.route('/start_job/<job_id>')
def scheduler_start_job(job_id):
    stop_job_api_url = f'{request.host_url}/scheduler/jobs/{job_id}/resume'
    response = requests.post(stop_job_api_url)

    if response.status_code == 200:
        logging.getLogger('apscheduler').info(f"The scheduler is starting job : {job_id}")
        return redirect(url_for('scheduler.scheduler_jobs'))

    logging.getLogger('apscheduler').error(f"The scheduler is failed to start job: {job_id}, response code: {response.status_code}")
    return "start failed"


@scheduler_blueprint.route('/stop_job/<job_id>')
def scheduler_stop_job(job_id):

    stop_job_api_url = f'{request.host_url}/scheduler/jobs/{job_id}/pause'
    response = requests.post(stop_job_api_url)

    if response.status_code == 200:
        logging.getLogger('apscheduler').info(f"The scheduler is stopping job : {job_id}")
        return redirect(url_for('scheduler.scheduler_jobs'))

    logging.getLogger('apscheduler').error(f"The scheduler is failed to stop job: {job_id}, response code: {response.status_code}")
    return "stop failed"


@scheduler_blueprint.route('/jobs_old')
def scheduler_jobs_old():
    # Add your logic for the individual job page
    # jobs = [{
    #     "args": [1, 2], "func": "app:job2", "id": "job2", "kwargs": {}, "max_instances": 3, "misfire_grace_time": 1,
    #     "name": "job2", "next_run_time": "2023-12-02T14:43:00.266004+00:00", "seconds": 45,
    #     "start_date": "2023-12-02T14:38:30.266004+00:00", "trigger": "interval"
    # }]

    # logging.getLogger('apscheduler').debug(f"url_jobs    : {url_for('scheduler.get_jobs')}")
    # logging.getLogger('apscheduler').debug(f"host prefix : {request.host_url}")
    #
    # # Fetch jobs data from the API endpoint
    # jobs_api_url = f'{request.host_url}scheduler/jobs'
    # response = urllib.request.urlopen(jobs_api_url)
    # data = response.read()
    #
    # if response.code == 200:
    #     # Parse the JSON response
    #     jobs = json.loads(data)
    #     for job in jobs:
    #         if job['next_run_time'] is None:
    #             job['stopped'] = True
    #         job["fails"] = scheduler_global_state["log"].get(job["id"], {"fails": 0}).get("fails")
    #         job["runs"] = scheduler_global_state["log"].get(job["id"], {"runs": 0}).get("runs") + job["fails"]
    # else:
    #     # Handle error cases
    #     jobs = []
    # jobs_ = scheduler.scheduler.get_jobs(jobstore="default", pending=True)
    jobs = scheduler_get_jobs_data()
    return render_template('list.html', jobs=jobs, active_tab2="JobList")


def get_job_data(form, field_filter=None):
    """
    :param form - form from POST request
    :param field_filter - optional
    :returns a dictionary
    Example:
    job_args = {
        'func': 'app:job1',
        'args': [101, 202],
        'trigger': 'interval',
        'seconds': 30,
        'id': 'new_job_bbb',
        'name': 'new_job_bbb',
        'replace_existing': True
    }
    """
    job_data = {}

    if field_filter is not None:
        for field_name in field_filter:
            if field_name == 'name':
                job_data['name'] = f'{form.get("job-name")}'
                job_data['id'] = f'{form.get("job-name")}'
            if field_name == 'id':
                job_data['id'] = f'{form.get("job-name")}'
            if field_name == 'jobstore':
                job_data['jobstore'] = form.get('jobstore')
        return job_data

    # Retrieve input values
    job_name = form.get('new-job-name')
    job_func = form.get('new-job-func')
    job_jobstore = form.get('new-job-jobstore')
    job_trigger = form.get('new-job-trigger')

    # Optional values
    job_func_args = None
    job_trigger_interval_unit = None
    job_trigger_interval_value = None
    job_trigger_hrs = None

    if job_trigger == 'interval':
        job_trigger_interval_unit = form.get('new-job-trigger-interval-options')
        if job_trigger_interval_unit == 'seconds':
            job_trigger_interval_value = form.get('new-job-trigger-sec')
        elif job_trigger_interval_unit == 'minutes':
            job_trigger_interval_value = form.get('new-job-trigger-min')
        else:
            raise Exception("The 'interval' value must be defined as 'minutes' or 'seconds'.")
    elif job_trigger == 'cron':
        job_trigger_hrs = form.get('timepicker-hour')
    else:
        err_msg = f"The 'trigger' must be defined as 'interval' or 'cron', current value is '{job_trigger}'."
        logging.getLogger('apscheduler').error(err_msg)
        raise Exception(err_msg)

    job_data = {
        'id': f'{job_name}',
        'name': f'{job_name}',
        'func': f'{job_func}',
        'jobstore': f'{job_jobstore}',
    }

    if job_trigger == 'interval':
        job_data['trigger'] = f'{job_trigger}'
        job_data[f'{job_trigger_interval_unit}'] = int(job_trigger_interval_value)
    elif job_trigger == 'cron':
        job_data['trigger'] = f'{job_trigger}'
        hh, mm = job_trigger_hrs.split(':')
        job_data['hour'] = int(hh)
        job_data['minute'] = int(mm)
        job_data['day_of_week'] = '*'

    logging.getLogger('apscheduler').info(f'Creating new job. {job_data}')

    return job_data


@scheduler_blueprint.route('/jobs', methods=['GET', 'POST', 'PUT', 'DELETE'])
def scheduler_jobs():
    """
        example of form fields data structure:
        job_args = {
            'func': 'app:job1',
            'args': [101, 202],
            'trigger': 'interval',
            'seconds': 30,
            'id': 'new_job_bbb',
            'name': 'new_job_bbb',
            'replace_existing': True
        }
    :return:
    """
    if request.method == 'POST':
        action_param = request.form.get('action_id') if request.form is not None else ""

        if action_param is not None and 'delete' == action_param:
            job_data_list = get_job_data(request.form, field_filter=['id', 'name', 'jobstore'])

            job_data_id = job_data_list['id'].split(",")
            job_data_name = job_data_list['name'].split(",")

            if len(job_data_id) == len(job_data_name):
                for idx in range(0, len(job_data_id)):
                    job_data = {
                        'id': job_data_id[idx],
                        'name': job_data_name[idx],
                        'jobstore': job_data_list['jobstore']
                        }
                    try:
                        scheduler.remove_job(job_data.get('name'), job_data.get('jobstore'))

                        logging.getLogger('apscheduler').info(f"A job '{job_data.get('id')}' was deleted successfully.")
                        flash(f"A new job '{job_data.get('id')}' was deleted successfully.", 'success')
                    except JobLookupError as lookup_err:
                        logging.getLogger('apscheduler').error(lookup_err)
                        flash(message=f"{lookup_err}", category='warning')
                    except Exception as ex:
                        logging.getLogger('apscheduler').error(f"Failed to delete job: '{job_data['id']}'.", ex)
                        flash(message=f"Failed to delete job: '{job_data['id']}'.", category='danger')
        elif action_param is not None and 'update' == action_param:
            try:
                job_data = get_job_data(request.form)
                scheduler.modify_job(**dict(job_data))
                logging.getLogger('apscheduler').info(f"A job '{job_data.get('id')}' was updated successfully.")
                flash(f"A job '{job_data.get('id')}' was updated successfully.", 'success')
            except Exception as ex:
                logging.getLogger('apscheduler').error(f"Failed to update job: '{job_data['id']}'.", ex)
                flash(message=f"Failed to update job: '{job_data['id']}'.", category='danger')
        elif action_param is not None and 'create' == action_param:
            job_data = get_job_data(request.form)
            job_data['args'] = [1010, 2020]
            job_data['func'] = f"app:{job_data['func']}"
            job_data['timezone'] = 'Israel'

            try:
                new_job = scheduler.add_job(**job_data)
                logging.getLogger('apscheduler').info(f"A new job '{new_job.id}' was created successfully.")
                flash(f"A new job '{new_job.id}' was created successfully.", 'success')
            except ConflictingIdError as conflict_err:
                logging.getLogger('apscheduler').error(conflict_err)
                flash(message=f"{conflict_err}", category='warning')
            except Exception as ex:
                logging.getLogger('apscheduler').error(f"Failed to create job: '{job_data['id']}'.", ex)
                flash(message=f"Failed to create job: '{job_data['id']}'.", category='danger')

        elif action_param is not None and 'read' == action_param:
            pass
        else:
            logging.getLogger('apscheduler').error(f'The action is not valid: "{action_param}"')

    elif request.method == 'PUT':
        job_data = get_job_data(request.form)
        scheduler.modify_job(job_data.get('name'), job_data.get('jobstore'), dict(job_data))

    elif request.method == 'DELETE':
        job_data = get_job_data(request.form, ['job_id', 'jobstore'])
        scheduler.remove_job(job_data.get('name'), job_data.get('jobstore'))

    jobs = scheduler_get_jobs_data()
    return render_template('list.html', jobs=jobs, active_tab2="JobList")


@scheduler_blueprint.route('/settings')
def scheduler_settings():
    # Fetch basic information about the webapp from the API endpoint
    jobs_api_url = f'{request.host_url}scheduler'
    response = urllib.request.urlopen(jobs_api_url)
    data = response.read()

    if response.code == 200:
        # Parse the JSON response
        scheduler_state = json.loads(data)

    scheduler_state['paused'] = scheduler_global_state['paused']

    # Load configuration from JSON file
    with open('config.json', 'r') as file:
        config_data = json.load(file)
        logging.getLogger('apscheduler').debug(f"scheduler configuration: ${config_data}")

    return render_template('schedule/settings.html', config_data=config_data,
                           scheduler_state=scheduler_state, active_tab="Scheduler", active_tab2="Settings")


def scheduler_get_jobs_data():
    # Add your logic for the individual job page
    # jobs = [{
    #     "args": [1, 2], "func": "app:job2", "id": "job2", "kwargs": {}, "max_instances": 3, "misfire_grace_time": 1,
    #     "name": "job2", "next_run_time": "2023-12-02T14:43:00.266004+00:00", "seconds": 45,
    #     "start_date": "2023-12-02T14:38:30.266004+00:00", "trigger": "interval"
    # }]
    logging.getLogger('apscheduler').debug(f"url_jobs    : {url_for('scheduler.get_jobs')}")
    logging.getLogger('apscheduler').debug(f"host prefix : {request.host_url}")

    # Fetch jobs data from the API endpoint
    jobs_api_url = f'{request.host_url}scheduler/jobs'
    response = urllib.request.urlopen(jobs_api_url)
    data = response.read()

    if response.code == 200:
        # Parse the JSON response
        jobs = json.loads(data)
        for job in jobs:
            if job["next_run_time"] is None:
                job['stopped'] = True
            job["fails"] = scheduler_global_state["log"].get(job["id"], {"fails": 0}).get("fails")
            job["runs"] = scheduler_global_state["log"].get(job["id"], {"runs": 0}).get("runs") + job["fails"]
        # jobs = json.dumps(jobs)
    else:
        # Handle error cases
        jobs = []

    # jobs_ = scheduler.scheduler.get_jobs(jobstore="default", pending=True)

    return jobs


def event_listener(event):
    global scheduler_global_state
    if event.code == EVENT_JOB_ERROR:
        logging.getLogger('apscheduler').error(f'The job "{event.job_id}" crashed :( {event.exception}')
        # if event.job_id not in scheduler_global_state["log"]:
        #     scheduler_global_state['log'][event.job_id] = {"runs": 0, "fails": 1, "events": []}
        # else:
        #     if len(scheduler_global_state["log"][event.job_id]["events"]) >= scheduler_global_state["max_log_entries"]:
        #         scheduler_global_state["log"][event.job_id]["events"].pop(0)
        #     scheduler_global_state["log"][event.job_id]["events"].append(event)
        #     scheduler_global_state['log'][event.job_id]['fails'] += 1

        try:
            job_log = JobLog(job_id=event.job_id, timestamp=event.scheduled_run_time)
            job_log.event = event
            job_log.fail_count += 1
            job_log.log_state = '{"test": 123, "complex": { "field_text": "text", "field_num": 999 }}'
            app.logs.add_job(job_log)

            update_scheduler_global_state(global_state=scheduler_global_state,
                                          jobstore=scheduler_global_state["jobstore"], job_id=event.job_id)

        except Exception as ex:
            logging.getLogger('apscheduler').error(f'Exception: {ex}')

    elif event.code == EVENT_JOB_REMOVED:
        logging.getLogger('apscheduler').info(f'The job "{event.job_id}" removed :)')
        scheduler_global_state['log'].pop(event.job_id)
    elif event.code == EVENT_JOB_ADDED:
        logging.getLogger('apscheduler').info(f'The job "{event.job_id}" added :)')
        scheduler_global_state['log'][event.job_id] = {"runs": 0, "fails": 0, "events": []}
    elif event.code == EVENT_JOB_MODIFIED:
        logging.getLogger('apscheduler').info(f'The job "{event.job_id}" modified :)')
    elif event.code == EVENT_JOB_SUBMITTED:
        logging.getLogger('apscheduler').info(f'The job "{event.job_id}" submitted :)')
    elif event.code == EVENT_JOB_EXECUTED:
        logging.getLogger('apscheduler').info(f'The job "{event.job_id}" executed :)')
        # if event.job_id not in scheduler_global_state["log"]:
        #     scheduler_global_state['log'][event.job_id] = {"runs": 1, "fails": 0, "events": []}
        # else:
        #     if len(scheduler_global_state["log"][event.job_id]["events"]) >= scheduler_global_state["max_log_entries"]:
        #         scheduler_global_state["log"][event.job_id]["events"].pop(0)
        #     scheduler_global_state["log"][event.job_id]["events"].append(event)
        #     scheduler_global_state['log'][event.job_id]['runs'] += 1

        try:
            job_log = JobLog(job_id=event.job_id, timestamp=event.scheduled_run_time)
            job_log.event = event
            job_log.run_count += 1
            job_log.log_state = '{"test": 123, "complex": { "field_text": "text", "field_num": 999 }}'
            app.logs.add_job(job_log)

            update_scheduler_global_state(global_state=scheduler_global_state,
                                          jobstore=scheduler_global_state["jobstore"], job_id=event.job_id)
        except Exception as ex:
            logging.getLogger('apscheduler').error(f'Exception: {ex}')
    else:
        logging.getLogger('apscheduler').info(f'The job "{event.job_id}" is successfully completed')


def init_scheduler(app_flask: Flask):

    global app
    app = app_flask

    # Load configuration from JSON file
    with open('config.json', 'r') as file:
        config_data = json.load(file)
        logging.getLogger('apscheduler').info(f"scheduler configuration: ${config_data}")

    # Update Flask app configuration
    app.config.update(config_data)
    if "SCHEDULER_JOBSTORES" in app.config and len([*app.config.get("SCHEDULER_JOBSTORES")]) > 0:
        scheduler_global_state["jobstore"] = [*app.config.get("SCHEDULER_JOBSTORES")][0]

    # Initialize and start the scheduler
    scheduler.init_app(app)
    scheduler.add_listener(event_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_ADDED |
                           EVENT_JOB_REMOVED | EVENT_JOB_MODIFIED | EVENT_JOB_SUBMITTED)
    scheduler.start()

    return scheduler


def init_job_log_store():
    # initializing with a database URL
    job_log_store = SQLAlchemyJobStore(url='sqlite:///joblogs.sqlite')
    job_log_store.start("myalias")
    # from models.job_log import JobLog
    # job_log = JobLog(job_id='1234')
    # job_log.event = 'Job Started'
    # job_log.log_state = '{"test": 123}'
    # # Adding a new job log
    # job_log_store.add_job(job_log)
    #
    # # Retrieving a job log
    # job_log = job_log_store.lookup_job(job_id=job_log.job_id)
    #
    # # Updating a job log
    # job_log.event = 'Job Completed'
    # job_log_store.update_job(job_log)

    return job_log_store


def init_scheduler_global_state():
    global scheduler_global_state
    logging.getLogger('apscheduler').\
        info(f"Initialize scheduler global state from {scheduler_global_state['jobstore']}:JobLog")
    scheduler_global_state = update_scheduler_global_state(global_state=scheduler_global_state,
                                                         jobstore=scheduler_global_state["jobstore"])


def update_scheduler_global_state(global_state: dict, jobstore: str, job_id=None):

    logging.getLogger('apscheduler').info(f"Update scheduler global state from {jobstore}:JobLog")

    try:
        if not scheduler.running:
            return global_state

        jobs = scheduler.scheduler.get_jobs()

        if job_id is not None:
            job_logs = app.logs.get_all_jobs_by_id(job_id)
        else:
            job_logs = app.logs.get_all_jobs()

        if job_logs is None or len(job_logs) == 0:
            for job in jobs:
                global_state['log'][job.id] = {"runs": 0, "fails": 0, "events": []}
            return global_state

        for job_log in job_logs:
            ###
            #
            # job_log = JobLog(job_id=event.job_id, timestamp=event.scheduled_run_time)
            # job_log.event = event
            # job_log.run_count += 1
            # job_log.log_state = '{"test": 123, "complex": { "field_text": "text", "field_num": 999 }}'
            #
            ###
            event = job_log.event

            logging.getLogger('apscheduler').info(f'The job "{event.job_id}" found in the job log.')
            logging.getLogger('apscheduler').debug(f'The job log attributes: '
                                                   f'id={job_log.id} '
                                                   f'job_id={job_log.job_id} '
                                                   f'fail_count={job_log.fail_count} '
                                                   f'run_count={job_log.run_count} '
                                                   f'timestamp={job_log.timestamp} ')

            if event.job_id not in global_state["log"]:
                global_state['log'][event.job_id] = {"runs": 0, "fails": 0, "events": []}
            else:
                if len(global_state["log"][event.job_id]["events"]) >= global_state["max_log_entries"]:
                    global_state["log"][event.job_id]["events"].pop(0)
            global_state["log"][event.job_id]["events"].append(event)
            if job_log.run_count > 0:
                global_state['log'][event.job_id]['runs'] += 1
            if job_log.fail_count > 0:
                global_state['log'][event.job_id]['fails'] += 1
            ###

        logging.getLogger('apscheduler').info(f"Success to update scheduler global state from {jobstore}:JobLog")
    except Exception as ex:
        logging.getLogger('apscheduler').error(f"Failed to update scheduler global state from {jobstore}:JobLog.", ex)

    return global_state


def get_scheduler_global_state(job_id):
    logging.getLogger('apscheduler').info(f"Get scheduler global state.")
    global_state = []

    try:
        global scheduler_global_state

        if not scheduler.running or job_id not in scheduler_global_state["log"]:
            logging.getLogger('apscheduler').info(f"No scheduler global state for job with id '{job_id}'.")
            return global_state

        global_state = scheduler_global_state["log"][job_id] # ["events"]
        logging.getLogger('apscheduler').info(f"Success to get scheduler global state.")

    except Exception as ex:
        logging.getLogger('apscheduler').error(f"Failed to get scheduler global state.", ex)

    return global_state
