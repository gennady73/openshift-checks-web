import json
import jinja2
from flask import Flask, render_template, request, jsonify, send_from_directory, flash, redirect, url_for, Blueprint, \
    get_flashed_messages
import os
import asyncio
import concurrent.futures

from models import ClusterCredential
from modules.async_task import perform_async_task, perform_async_task_2
from datetime import datetime
from config import Config
from modules.logger.custom_formatter import CustomFormatter
from modules.schedule.app_scheduler import scheduler_blueprint
from modules.schedule.app_scheduler import init_scheduler, init_job_log_store, init_scheduler_global_state
from modules.editor.app_code_editor import init_code_editor, flaskcode_blueprint, editor_blueprint
from modules.occode import blueprint as occode_blueprint
import logging, logging.config
import yaml
from modules.security import oc_login, oc_login2
from collections import OrderedDict
from modules.security import cluster_credentials

app = Flask(__name__)

app.config.from_object(Config)

with open('logger.json', 'r') as file:
    logger_config_json = json.load(file)

logging.config.dictConfig(logger_config_json)

app.secret_key = "anyStringHereForFlashMessages"

static_default_blueprint = \
    Blueprint('static_default_blueprint', __name__, static_folder='static/*')
static_ext1_blueprint = \
    Blueprint('static_ext1_blueprint', __name__, static_folder='../openshift-checks')
static_ext2_blueprint = \
    Blueprint('static_ext2_blueprint', __name__, static_folder='../openshift-checks/local-web-resources')

app.register_blueprint(static_default_blueprint)
app.register_blueprint(static_ext1_blueprint)
app.register_blueprint(static_ext2_blueprint)
app.register_blueprint(scheduler_blueprint, url_prefix='/schedule')
app.register_blueprint(editor_blueprint, url_prefix='/editor')
#app.register_blueprint(flaskcode_blueprint, url_prefix='/flaskcode')
app.register_blueprint(occode_blueprint, url_prefix='/occode')

my_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader(['../openshift-checks',
                             '../openshift-checks/local-web-resources',
                             '../openshift-checks-web',
                             '../openshift-checks-web/static',
                             '../openshift-checks-web/templates',
                             'templates/schedule',
                             'templates/flaskcode',
                             'templates/occode',
                             'templates/home']),
])

app.jinja_loader = my_loader

scheduler = None
logs = None

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
from types import SimpleNamespace
app.cluster_info_list = []
app.cluster_info_list = get_clusters_from_datastore()

@app.route('/')
def home():
    # timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # flash(f'Async Task Completed Successfully at {timestamp}', 'success')
    clusters = get_clusters_from_datastore() # get_clusters_from_kubeconfigs()
    return render_template('home/home.html', active_tab="Home", active_tab2="LastCheckResults",
                           cluster_info_list=cluster_info_list,
                           clusters=clusters)


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

@app.route('/settings/?',  methods=['GET', 'POST'])
def settings():
    # Add your logic for the settings page
    # Load configuration from JSON file
    with open('config.json', 'r') as file:
        config_data = json.load(file)
        logging.getLogger('root').debug(f"scheduler configuration:\n${config_data}")

    # cluster_info_list = list([
    #     {
    #         "id": 1,
    #         "name": "dev-cluster",
    #         "server": "https://api.dev-cluster.example.com:6443",
    #         "token": "sha256~abc123devtoken",
    #         "certificate": "XXX",
    #         "user": "developer",
    #         "namespace": "dev-namespace",
    #         "insecure": True,
    #         "sa": "dev-service-account"
    #     },
    #     {
    #         "id": 2,
    #         "name": "test-cluster",
    #         "server": "https://api.test-cluster.example.com:6443",
    #         "token": "sha256~test456token",
    #         "certificate": "YYY",
    #         "user": "tester",
    #         "namespace": "test-namespace",
    #         "insecure": False,
    #         "sa": "test-service-account"
    #     },
    #     {
    #         "id": 3,
    #         "name": "prod-cluster",
    #         "server": "https://api.prod-cluster.example.com:6443",
    #         "token": "sha256~prod789token",
    #         "certificate": "ZZZ",
    #         "user": "admin",
    #         "namespace": "prod",
    #         "insecure": False,
    #         "sa": "admin-service-account"
    #     }
    # ])
    #cluster_info_list = []

    credentials = app.cluster_creds.list_credentials()
    credentials_list = [cluster.to_dict() for cluster in credentials]
    global cluster_info_list
    cluster_info_list = credentials_list

    clusters = OrderedDict()
    for cluster in cluster_info_list:
        server = cluster["server"]
        # Deduplicate by server URL
        if server not in clusters:
            clusters[server] = cluster.get("name")

    clusters = list(clusters.values())

    if request.method == 'POST':

        # name = "dev-cluster",
        # server = "https://api.dev-cluster.example.com:6443",
        # token = "sha256~abc123devtoken",
        # certificate = "---CERTIFICATE---",
        # user = "developer",
        # namespace = "dev-namespace",
        # insecure = True,
        # sa = "dev-service-account"
        #
        # cluster = ClusterCredential(
        #     name="dev-cluster",
        #     server="https://api.dev-cluster.example.com:6443",
        #     token="sha256~abc123devtoken",
        #     certificate="---CERTIFICATE---",
        #     user="developer",
        #     namespace="dev-namespace",
        #     insecure=True,
        #     sa="dev-service-account"
        # )

        form_data = request.form.to_dict()
        #form_data['insecure'] = form_data['insecure']=='on'
        clean_data = {}
        for k, v in form_data.items():
            if k == 'action':
                continue
            if k == 'insecure':
                clean_data[k] = True if (form_data['insecure'] and form_data['insecure']=='on') else False
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
                credential_id=cluster.id
            )
    return render_template('home/settings.html',
                           config_data=config_data,
                           cluster_info_list=cluster_info_list,
                           clusters=clusters,
                           active_tab="Home", active_tab2="Settings")


@app.route('/login')
def login():
    # Add logic for login
    return "Login page"


@app.route('/logout')
def logout():
    # Add logic for logout
    return "Logout page"

@app.route("/login-cluster", methods=["POST"])
def login_cluster():
    cluster_name = request.json.get("cluster")
    if not cluster_name:
        return jsonify({"error": "No cluster selected"}), 400

    #TODO response = oc_login(cluster_name)
    response = oc_login2(cluster_name, app.cluster_creds)
    return jsonify(response)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/osc.json')
def osc_json():
    return send_from_directory(static_ext1_blueprint.static_folder, 'osc.json')


@app.route('/async-task', methods=['POST'])
async def async_task_route():
    try:
        cluster_name = request.json.get('cluster')
        loop = asyncio.get_event_loop()
        #result = await asyncio.wait_for(asyncio.gather(perform_async_task()), timeout=15)
        login_attributes = oc_login2(cluster_name=cluster_name, credentials_store=app.cluster_creds)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        flash(f'Task execution is scheduled at {timestamp}.', 'success')
        result = await asyncio.wait_for(asyncio.gather(perform_async_task_2(cluster_name, login_attributes=login_attributes)), timeout=600)
        #result.decode('utf-8')
        #timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #flash(f'Task execution is scheduled at {timestamp}. Result:{result}', 'success')
    except concurrent.futures.TimeoutError:
        flash('Task timed out!', 'error')
    except Exception as e:
        flash(f'Task Error: {e}', 'error')

    #return redirect(url_for('home')
    #return render_template('osc.local.html')
    #home_tab_nav = render_template('partials/home/tab_nav.html')
    #result_container = render_template('osc.local.html')

    return jsonify({
        "home_tab_nav": render_template('partials/home/tab_nav.html'),
        "result_container": render_template('osc.local.html'),
        "notification": get_flashed_messages(True)
    })

@app.route('/results', methods=['POST', 'GET'])
async def results_route():

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

    pass

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