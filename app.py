import json
from pathlib import Path
from urllib.parse import unquote

import jinja2
from flask import Flask, render_template, request, jsonify, send_from_directory, flash, redirect, url_for, Blueprint, \
    get_flashed_messages, session
import os
import asyncio
import concurrent.futures
from asyncio import AbstractEventLoop

from flask_session import Session

from models import ClusterCredential
from modules.async_task import perform_async_task, perform_async_task_2
from datetime import datetime
from config import Config
from modules.logger.custom_formatter import CustomFormatter
from modules.schedule.app_scheduler import scheduler_blueprint
from modules.schedule.app_scheduler import init_scheduler, init_job_log_store, init_scheduler_global_state
from modules.editor.app_code_editor import init_code_editor, flaskcode_blueprint, editor_blueprint
from modules.occode import blueprint as occode_blueprint
from modules.diff.check_results_diff import diff_blueprint, init_diff
import logging, logging.config
import yaml
from modules.security import oc_login, oc_login2
from collections import OrderedDict
from modules.security import cluster_credentials
import re

app = Flask(__name__)

app.config.from_object(Config)
Session(app)

with open('logger.json', 'r') as file:
    logger_config_json = json.load(file)

logging.config.dictConfig(logger_config_json)

app.secret_key = "anyStringHereForFlashMessages"

static_default_blueprint = \
    Blueprint('static_default_blueprint', __name__, static_folder='static')
static_ext1_blueprint = \
    Blueprint('static_ext1_blueprint', __name__, static_folder='../openshift-checks')
static_ext2_blueprint = \
    Blueprint('static_ext2_blueprint', __name__, static_folder='../openshift-checks/local-web-resources')
static_data_blueprint = \
    Blueprint('static_data_blueprint', __name__, static_folder='data')
static_local_wr_blueprint = \
    Blueprint('static_local_wr_blueprint', __name__, static_folder='local-web-resources')


app.register_blueprint(static_default_blueprint)
app.register_blueprint(static_ext1_blueprint)
app.register_blueprint(static_ext2_blueprint)
app.register_blueprint(scheduler_blueprint, url_prefix='/schedule')
app.register_blueprint(editor_blueprint, url_prefix='/editor')
app.register_blueprint(diff_blueprint, url_prefix='/diff')
app.register_blueprint(occode_blueprint, url_prefix='/occode')
app.register_blueprint(static_data_blueprint)
app.register_blueprint(static_local_wr_blueprint)

my_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader(['../openshift-checks',
                             '../openshift-checks/local-web-resources',
                             '../openshift-checks-web',
                             '../openshift-checks-web/static',
                             '../openshift-checks-web/templates',
                             '../openshift-checks-web/local-web-resources',
                             'templates/schedule',
                             'templates/flaskcode',
                             'templates/occode',
                             'templates/home',
                             'templates/diff']),
])

app.jinja_loader = my_loader

scheduler = None
logs = None

# move to home module
CHECK_RESULT_DIR_NAME = 'results' # in future releases, this value must be retrieved from the app config.

# The default name pattern of "result" file: <YYYYMMDD>-<HHMMSS>-<CLUSTER_ID>-<CLUSTER_NAME>.json
RESULT_DIR_REGEX_PATTERN = r"([\d]{8}-[\d]{6})(-)[0-9]+(-)([\w\d\-]+)(.json)"

STATIC_DATA_BLUEPRINT:Blueprint|None = None
CHECK_RESULT_PATH: str|None = None

RESULT_DIR_REGEX = re.compile(RESULT_DIR_REGEX_PATTERN)

#global STATIC_DATA_BLUEPRINT
#STATIC_DATA_BLUEPRINT = app.blueprints.get('static_data_blueprint')

#global CHECK_RESULT_PATH
#CHECK_RESULT_PATH = os.path.join(os.path.abspath(STATIC_DATA_BLUEPRINT.static_folder), CHECK_RESULT_DIR_NAME)
# end move

def init_home(fapp:Flask):
    # move to home module
    global STATIC_DATA_BLUEPRINT
    STATIC_DATA_BLUEPRINT = fapp.blueprints.get('static_data_blueprint')

    global CHECK_RESULT_PATH
    CHECK_RESULT_PATH = os.path.join(os.path.abspath(STATIC_DATA_BLUEPRINT.static_folder), CHECK_RESULT_DIR_NAME)
    # end move

# OLD VERSION
# def json_files_list(directory: str, pattern: str | None = None) -> list:
#     if pattern is None or pattern.strip() == '':
#         pattern = RESULT_DIR_REGEX_PATTERN # default
#     regex = re.compile(pattern)
#
#     # List files, filter by .json and the regex pattern
#     matched_files = [
#         os.path.join(directory, f)
#         for f in os.listdir(directory)
#         if f.endswith('.json') and regex.match(f)
#     ]
#
#     matched_file_names = []
#     for f in matched_files:
#         path = Path(f)
#         matched_file_names.append(path.name)
#
#     matched_file_names.sort(reverse=True)
#     return matched_file_names

def json_files_list(directory: str, pattern: str | None = None, start_date=None, end_date=None) -> list:
    if pattern is None or pattern.strip() == '':
        pattern = RESULT_DIR_REGEX_PATTERN
    regex = re.compile(pattern)

    matched_artifacts = []

    for f in os.listdir(directory):
        if not f.endswith('.json'):
            continue

        match = regex.match(f)
        if match:
            # Extract the timestamp group (e.g., '20260326-101026')
            timestamp_str = match.group(1)
            file_dt = datetime.strptime(timestamp_str, "%Y%m%d-%H%M%S")

            # Apply time boundaries from the AJAX request
            if start_date and file_dt < start_date:
                continue
            if end_date and file_dt > end_date:
                continue

            file_path = os.path.join(directory, f)
            is_baseline = False

            # Open the JSON file to check for the baseline flag
            try:
                with open(file_path, 'r') as json_file:
                    data = json.load(json_file)
                    # Check if metadata exists and is_baseline is true
                    if data.get('metadata', {}).get('is_baseline') is True:
                        is_baseline = True
            except Exception as e:
                print(f"Error reading artifact {f}: {e}")

            matched_artifacts.append({
                'filename': f,
                'is_baseline': is_baseline,
                'execution_date': file_dt
            })

    # Sort descending (newest first) based on the exact execution date
    matched_artifacts.sort(key=lambda x: x['execution_date'], reverse=True)

    # Strip the datetime object before returning the JSON payload to the frontend
    return [{"filename": item["filename"], "is_baseline": item["is_baseline"]} for item in matched_artifacts]



@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y/%m/%d %H:%M:%S'):
    """Convert a datetime to a different format."""
    if value is None or len(value) == 0:
        return ""
    dtf = datetime.fromisoformat(value)
    return dtf.strftime(format)


@app.template_filter('timeformat')
def datetimeformat(value, format='%H:%M:%S'):
    """Convert a time to a different format."""
    if value is None or len(value) == 0:
        return ""
    # tf = datetime.fromisoformat(value).time()
    tf = datetime.strptime(value, '%H%M')
    return tf.strftime(format)


def get_clusters_from_kubeconfigs()->list:
    kubeconfig_env = os.environ.get("KUBECONFIG", "~/.kube/config")
    kubeconfigs = []

    for path in kubeconfig_env.split(":"):
        expanded_path = os.path.expanduser(path.strip())
        if os.path.isfile(expanded_path):
            kubeconfigs.append(expanded_path)

    clusters = OrderedDict()

    for config_file in kubeconfigs:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
            for c in config.get("clusters", []):
                server = c["cluster"]["server"]
                # Deduplicate by server URL
                if server not in clusters:
                    clusters[server] = c["name"]

    return list(clusters.values())


def get_clusters_from_datastore()->list:
    credentials = app.cluster_creds.list_credentials()
    credentials_list = [cluster.to_dict() for cluster in credentials]

    clusters = OrderedDict()
    for cluster in credentials_list:
        server = cluster["server"]
        # Deduplicate by server URL
        if server not in clusters:
            clusters[server] = cluster.get("name")

    clusters = list(clusters.values())
    #return clusters
    global cluster_info_list
    cluster_info_list = credentials_list
    return cluster_info_list

app.cluster_creds = cluster_credentials.init_cluster_credentials_store()
app.clusters = get_clusters_from_datastore() # get_clusters_from_kubeconfigs()
app.cluster_info_list = []
app.cluster_info_list = get_clusters_from_datastore()

@app.route('/baseline', methods=['POST'])
async def toggle_baseline():
    """ This function experimental and yet under construction. """

    # --- 1. Receive & validate JSON ---
    try:
        request_json = request.get_json(force=True)
    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400

    # --- 2. Extract metadata ---
    cluster_id = request_json.get("cluster_id", "unknown")
    result_file_name = request_json.get("selected_result", "osc.json")

    # --- Optional: validate required fields ---
    if cluster_id == "unknown":
        return jsonify({"error": "Missing cluster_id"}), 400

    if result_file_name == "osc.json":
        return jsonify({"error": "Missing selected_result"}), 400

    output = {}
    # --- Set "is_baseline": true(or false) in the "metadata section" if JSON file ---
    try:
        # Read the JSON file from the path where results are stored.
        result_file_name_path = os.path.join(CHECK_RESULT_PATH, result_file_name)

        with open(result_file_name_path, 'r') as f:
            output = json.load(f)

        if "is_baseline" in output["metadata"]:
            output["metadata"]["is_baseline"] = not output["metadata"]["is_baseline"]
        else:
            output["metadata"]["is_baseline"] = True

    except FileNotFoundError as error:
        flash(f'The baseline toggle is failed. {error}', 'error')

    return jsonify({
            "is_baseline": output["metadata"]["is_baseline"],
            "notification": get_flashed_messages(True),
        }), 200


@app.route('/data/selected', methods=['GET'])
def check_result_file_name():
    result_file_name = session.get('selected_result', 'osc.json')
    return jsonify(result_file_name)

@app.route('/data/list', methods=['GET'])
def check_result_data_list():
    json_list = json_files_list(directory=CHECK_RESULT_PATH, pattern=RESULT_DIR_REGEX_PATTERN)
    return jsonify(json_list)


@app.route('/<filename>.json', methods=['GET'])
def get_json_data(filename):

    # static_ext1_blueprint = app.blueprints.get('static_ext1_blueprint')
    # if filename is not None:
    #     json_file_path = os.path.join(os.path.abspath(static_ext1_blueprint.static_folder), f"{filename}.json")
    # else:
    #     json_file_path = os.path.join(os.path.abspath(static_ext1_blueprint.static_folder), request.path.replace('/diff/',''))

    if filename is not None:
        json_file_name = f"{filename}.json"
    else:
        json_file_name = request.path.replace('/diff/','')

    # if json_file_name.endswith('_diff.json') and DIFF_RESULT_DIR_REGEX.match(json_file_name):
    #     directory = DIFF_RESULT_PATH
    # el
    if (not json_file_name.endswith('_diff.json') and RESULT_DIR_REGEX.match(json_file_name)) or json_file_name == 'osc.json':
        directory = CHECK_RESULT_PATH
    else:
        return 404

    json_file_path = os.path.join(directory, f"{json_file_name}")

    try:
        # Open the file and load the data into a Python dictionary/list
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        session['selected_result'] = json_file_name
        # Return the Python object as a JSON response
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Data file not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Error decoding JSON"}), 500

@app.route('/')
def home():
    clusters = get_clusters_from_datastore() # get_clusters_from_kubeconfigs()
    selected_cluster = session.get('selected_cluster', '0')

    list_json = json_files_list(directory=CHECK_RESULT_PATH, pattern=RESULT_DIR_REGEX_PATTERN)
    query_string = request.query_string.decode()

    if query_string != '':
        if query_string is not None and "?" in request.path:
            raise ValueError("Query string is defined in the path and as an argument")
        rfn = query_string.split("json=")[1] if len(query_string.split("json=")) == 2 else 'osc.json'

        if rfn in list_json:
            result_file_name = rfn
            session['selected_result'] = result_file_name
        elif next((item for item in list_json if item['filename'] == f"{rfn}"), None) is not None:
            result_file_name = rfn
            session['selected_result'] = result_file_name
        else:
            result_file_name = 'osc.json' # empty report
            flash(f'Report "{rfn}" not found', 'warning')
    else:
        result_file_name = session.get('selected_result', 'osc.json') # real or empty report


    return render_template('home/home.html', active_tab="Home", active_tab2="LastCheckResults",
                           cluster_info_list=cluster_info_list,
                           clusters=clusters,
                           selected_cluster=selected_cluster,
                           jsonFile = result_file_name,
                           list_json = list_json)


@app.route('/cluster_info/<cluster_id>')
def cluster_info(cluster_id):
    global cluster_info_list
    if not cluster_info_list:
        cluster_info_list = list([
                {
                    "id": 1,
                    "name": "dev-cluster",
                    "server": "https://api.dev-cluster.example.com:6443",
                    "token": "sha256~abc123devtoken",
                    "user": "developer",
                    "namespace": "dev-namespace",
                    "insecure": True,
                    "sa": "dev-service-account"
                },
                {
                    "id": 2,
                    "name": "test-cluster",
                    "server": "https://api.test-cluster.example.com:6443",
                    "token": "sha256~test456token",
                    "user": "tester",
                    "namespace": "test-namespace",
                    "insecure": False,
                    "sa": "test-service-account"
                },
                {
                    "id": 3,
                    "name": "prod-cluster",
                    "server": "https://api.prod-cluster.example.com:6443",
                    "token": "sha256~prod789token",
                    "user": "admin",
                    "namespace": "prod",
                    "insecure": False,
                    "sa": "admin-service-account"
                }
            ]
        )

    return cluster_info_list

@app.route('/settings',  methods=['GET', 'POST'])
def settings():
    """
        Args:
        POST data example:

                name = "dev-cluster",
        server = "https://api.dev-cluster.example.com:6443",
        token = "sha256~abc123devtoken",
        certificate = "---CERTIFICATE---",
        user = "developer",
        namespace = "dev-namespace",
        insecure = True,
        sa = "dev-service-account"

        cluster = ClusterCredential(
            name="dev-cluster",
            server="https://api.dev-cluster.example.com:6443",
            token="sha256~abc123devtoken",
            certificate="---CERTIFICATE---",
            user="developer",
            namespace="dev-namespace",
            insecure=True,
            sa="dev-service-account"
        )

        The 'cluster_info_list' example:

        cluster_info_list = list([
            {
                "id": 1,
                "name": "dev-cluster",
                "server": "https://api.dev-cluster.example.com:6443",
                "token": "sha256~abc123devtoken",
                "certificate": "XXX",
                "user": "developer",
                "namespace": "dev-namespace",
                "insecure": True,
                "sa": "dev-service-account"
            },
            {
                "id": 2,
                "name": "test-cluster",
                "server": "https://api.test-cluster.example.com:6443",
                "token": "sha256~test456token",
                "certificate": "YYY",
                "user": "tester",
                "namespace": "test-namespace",
                "insecure": False,
                "sa": "test-service-account"
            },
            {
                "id": 3,
                "name": "prod-cluster",
                "server": "https://api.prod-cluster.example.com:6443",
                "token": "sha256~prod789token",
                "certificate": "ZZZ",
                "user": "admin",
                "namespace": "prod",
                "insecure": False,
                "sa": "admin-service-account"
            }
        ])
    """

    # Load configuration from JSON file
    with open('config.json', 'r') as f:
        config_data = json.load(f)
        logging.getLogger('root').debug(f"scheduler configuration:\n${config_data}")

    # credentials = app.cluster_creds.list_credentials()
    # credentials_list = [cluster.to_dict() for cluster in credentials]
    # global cluster_info_list
    # cluster_info_list = credentials_list
    #
    # clusters = OrderedDict()
    # for cluster in cluster_info_list:
    #     cluster_uuid = cluster["uuid"]
    #     # server = cluster["server"] # Deduplicate by server URL
    #     # if server not in clusters:
    #     #     clusters[server] = cluster.get("name")
    #     if  cluster_uuid not in clusters:
    #         clusters[cluster_uuid] = cluster.get("name")
    #
    # clusters = list(clusters.values())

    if request.method == 'POST':
        form_data = request.form.to_dict()
        #form_data['insecure'] = form_data['insecure']=='on'
        clean_data = {}
        for k, v in form_data.items():
            if k == 'action':
                continue
            if k == 'insecure':
                # In PatternFly v3, a checkbox component is typically managed within a React state
                # to determine its "on" (checked) or "off" (unchecked) value.
                clean_data[k] = True if (form_data['insecure'] and form_data['insecure']=='True') else False
            else:
                clean_data[k] = v

        cluster = ClusterCredential(**clean_data)

        if form_data.get('action') == 'create':
            app.cluster_creds.add_credential(
                credential=cluster
            )
        elif form_data.get('action') == 'update':
            app.cluster_creds.update_credential(
                credential=cluster
            )
        elif form_data.get('action') == 'delete':
            app.cluster_creds.delete_credential(
                credential_id=cluster.uuid
            )

    credentials = app.cluster_creds.list_credentials()
    credentials_list = [cluster.to_dict() for cluster in credentials]
    global cluster_info_list
    cluster_info_list = credentials_list

    clusters = OrderedDict()
    for cluster in cluster_info_list:
        cluster_uuid = cluster["uuid"]
        # server = cluster["server"] # Deduplicate by server URL
        # if server not in clusters:
        #     clusters[server] = cluster.get("name")
        if  cluster_uuid not in clusters:
            clusters[cluster_uuid] = cluster.get("name")

    clusters = list(clusters.values())

    selected_cluster = session.get('selected_cluster', '0')
    return render_template('home/settings.html',
                           config_data=config_data,
                           cluster_info_list=cluster_info_list,
                           clusters=clusters,
                           active_tab="Home", active_tab2="Settings", selected_cluster=selected_cluster)


@app.route('/local-web-resources/<path:subpath>', methods=['GET'])
def local_web_resources(subpath):
    """
    Retrieves resources (*.css, *,js, etc.) which initially source was web.
    Intentionally, used for disconnected environments.
    """
    ru = request.url.replace('diff/', '')
    return redirect(unquote(ru))


@app.route('/login')
def login():
    """ Implements logic for login process """
    return "Login page"


@app.route('/logout')
def logout():
    """ Implements logic for logout process """
    return "Logout page"


@app.route("/login-cluster", methods=["POST"])
def login_cluster():
    """ Implements logic for login into the examined cluster process. """
    selected_cluster = request.json.get("cluster")
    if not selected_cluster:
        flash(f'No cluster selected', 'error')
        return jsonify({
            "error": "No cluster selected",
            "notification": get_flashed_messages(True),
        }), 400

    session['selected_cluster'] = selected_cluster
    response = oc_login2(selected_cluster, app.cluster_creds)
    return jsonify(response)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/osc.json')
def osc_json():
    return send_from_directory(static_ext1_blueprint.static_folder, 'osc.json')


def list_json_files(directory):
    pattern = r"([\d]{8}-[\d]{6})(-)[0-9]+(-)([\w\d\-]+)(.json)"
    regex = re.compile(pattern)

    # List files, filter by .json and the regex pattern
    matched_files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith('.json') and regex.match(f)
    ]

    matched_file_names = []
    for f in matched_files:
        path = Path(f)
        matched_file_names.append(path.name)

    return matched_file_names

@app.route('/<filename>.json')
def get_json(filename):
    if "/" in filename or "\\" in filename or filename == "..":
        return (404)
    session['selected_result'] = filename
    return send_from_directory(static_ext1_blueprint.static_folder, f"{filename}.json")


@app.route('/async-task', methods=['POST'])
async def async_task_route():
    output = {}
    result_file_name = None
    list_json = []

    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cluster_id = request.json.get('cluster_id')
        list_json = json_files_list(directory=CHECK_RESULT_PATH, pattern=RESULT_DIR_REGEX_PATTERN)
        result_file_name = session.get('selected_result', 'osc.json')

        if cluster_id is None or str(cluster_id).strip() == '':
            flash(f'Task execution failed at {timestamp}. Select cluster on order to run checks', 'error')
            result_file_name = 'osc.json'
            return jsonify({
                "home_tab_nav": render_template('partials/home/tab_nav.html'),
                "result_container": render_template('results.html'),
                "notification": get_flashed_messages(True),
                "json_check_list": list_json,
                "json_check_file": result_file_name,
            })

        # FIX: "how it may be used here?"
        loop:AbstractEventLoop|None = asyncio.get_event_loop()

        if loop is not None:
            logging.getLogger('root').debug(f"asyncio event loop is {str("" if loop.is_running() else "not")} running.")
        else:
            logging.getLogger('root').debug(f"asyncio event loop is not exists.")

        login_attributes = oc_login2(cluster_uuid=cluster_id, credentials_store=app.cluster_creds)

        login_response = (login_attributes.get('error', '')).strip('\n')

        if len(login_response):
            flash(f'Task execution failed at {timestamp}. {login_response}', 'error')
            result_file_name = 'osc.json'
            return jsonify({
                "home_tab_nav": render_template('partials/home/tab_nav.html'),
                "result_container": render_template('results.html'),
                "notification": get_flashed_messages(True),
                "json_check_list": list_json,
                "json_check_file": result_file_name,
            })

        else:
            flash(f'Task execution is scheduled at {timestamp}.', 'success')

            result = await asyncio.wait_for(asyncio.gather(
                perform_async_task_2(cluster_name=cluster_id,
                                    login_attributes=login_attributes,
                                    timestamp=timestamp,
                                     dest_dir=CHECK_RESULT_PATH)),
                timeout=600)
            result_output, result_file_name = result[0]

            try:
                # Read the JSON file from the path where results are stored.
                result_file_name_out_path = os.path.join(CHECK_RESULT_PATH, result_file_name)
                with open(result_file_name_out_path, 'r') as f:
                    output = json.load(f)

                # Write metadata the "baseline" tag, default false
                output["metadata"]["is_baseline"] = False
                with open('data.json', 'w') as f_out:
                    json.dump(output, f_out, indent=4)

            except FileNotFoundError as error:
                flash(f'Task execution failed at {timestamp}. {error}', 'error')

            session['selected_result'] = result_file_name

    except concurrent.futures.TimeoutError:
        flash('Task timed out!', 'error')
    except Exception as e:
        flash(f'Task Error: {e}', 'error')

    return jsonify({
        "home_tab_nav": render_template('partials/home/tab_nav.html'),
        "result_container": render_template('results.html', jsonFile=result_file_name, list_json=list_json),
        "notification": get_flashed_messages(True),
        "json_check_list": list_json,
        "json_check_file": result_file_name,
        "data": output,
    })


@app.route('/results', methods=['POST', 'GET'])
async def results_route():
    """ This function experimental and yet under construction. """

    #db_session: Session = SQLAlchemyJobStore.get_session('risu_results')

    if request.method == 'POST':
        # --- 1. Receive & validate JSON ---
        try:
            risu_json = request.get_json(force=True)
        except Exception as e:
            return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400

        # --- 2. Extract metadata ---
        cluster_name = risu_json.get("cluster_name") or risu_json.get("cluster", "unknown")
        risu_version = risu_json.get("version", "unknown")

        # Optional: validate required fields
        if not cluster_name:
            return jsonify({"error": "Missing cluster_name"}), 400
    elif request.method == 'GET':
        # --- 5. Retrieve results ---
        cluster_name = request.args.get('cluster')
        since = request.args.get('since')  # optional timestamp filter

        # query = db_session.query(RisuResult)
        # if cluster_name:
        #     query = query.filter(RisuResult.cluster_name == cluster_name)
        # if since:
        #     try:
        #         since_dt = datetime.fromisoformat(since)
        #         query = query.filter(RisuResult.run_timestamp >= since_dt)
        #     except ValueError:
        #         return jsonify({"error": "Invalid 'since' format, expected ISO8601"}), 400
        #
        # records = query.order_by(RisuResult.run_timestamp.desc()).all()
        records = []

        # --- render result partial for UI comparison ---
        html_partial = render_template(
            'partials/result_container.html',
            results=[r.as_dict() for r in records]
        )

        return jsonify({
            "result_container": html_partial,
            # "count": len(records)
        })

    return "This feature is not yet implemented.", 501


@app.route('/extchecks/')
def extchecks():
    filenames = os.listdir('extchecks')
    return render_template('extchecks_list.html', files=filenames)


@app.route('/extchecks/<path:filename>')
def extcheck(filename):
    return send_from_directory(
        os.path.abspath('extchecks'),
        filename,
        as_attachment=True
    )


def job1(var_one, var_two):
    """Demo job function.

    :param var_one:
    :param var_two:
    """
    logging.getLogger('root').debug(f"job1: {str(var_one)}, {str(var_two)}")
    logging.getLogger('root').debug(f"job1: {str(var_one)} + {str(var_two)} = {var_one + var_two}")


def job2(var_one, var_two):
    """Demo job function.

    :param var_one:
    :param var_two:
    """
    with scheduler.app.app_context():
        # logging.getLogger('root').debug(f"job2: {str(var_one)} + {str(var_two)} = {var_one + var_two}")
        # logging.getLogger('root').debug(f"job2: {str(var_one)} / {str(0)} = {var_one / 0}")

        import random

        # Generate a random number
        random_number = random.randint(1, 100)  # Adjust the range as needed

        # Check if the random number is odd or even
        if random_number % 2 == 0:
            logging.getLogger('root').debug(f"{random_number} is an even number.")
            logging.getLogger('root').debug(f"job2: {str(var_one)} + {str(var_two)} = {var_one + var_two}")
        else:
            logging.getLogger('root').debug(f"{random_number} is an odd number.")
            logging.getLogger('root').debug(f"job2: {str(var_one)} / {str(0)} = {var_one / 0}")

init_home(app) # move to home
log_formatter:logging.Formatter = CustomFormatter()
init_code_editor(app)

# for handler in app.logger.root.handlers:
#     handler.setFormatter(log_formatter)
#
# handler = logging.StreamHandler()
# handler.setFormatter(log_formatter)
# logging.getLogger('root').addHandler(handler)
logging.getLogger('root').setLevel(logging.DEBUG)
logging.getLogger('root').info("test")
logging.getLogger('root').warning("test")
logging.getLogger('root').error("test")
logging.getLogger('root').critical("test")
logging.getLogger('root').fatal("test")
logging.getLogger('root').debug("test")
# logging.getLogger('apscheduler').addHandler(handler)
# logging.getLogger('apscheduler').info("test")

app.logs = init_job_log_store()
app.scheduler = init_scheduler(app)
init_scheduler_global_state()
init_diff(app)

# @app.teardown_appcontext
# def shutdown_credential_store(exception=None):
#     app.cluster_creds.shutdown()

if __name__ == '__main__':

    app.run(host=Config.FLASK_RUN_HOST, port=Config.FLASK_RUN_PORT)
    # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass