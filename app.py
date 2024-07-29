import json
import jinja2
from flask import Flask, render_template, request, jsonify, send_from_directory, flash, redirect, url_for, Blueprint
import os
import asyncio
import concurrent.futures
from modules.async_task import perform_async_task
from datetime import datetime
from config import Config
from modules.schedule.app_scheduler import scheduler_blueprint
from modules.schedule.app_scheduler import init_scheduler, init_job_log_store, init_scheduler_global_state

app = Flask(__name__)

app.config.from_object(Config)
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

my_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader(['../openshift-checks',
                             '../openshift-checks/local-web-resources',
                             '../openshift-checks-web',
                             '../openshift-checks-web/static',
                             '../openshift-checks-web/templates',
                             'templates/schedule']),
])
app.jinja_loader = my_loader

scheduler = None


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


@app.route('/')
def home():
    # timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # flash(f'Async Task Completed Successfully at {timestamp}', 'success')
    return render_template('b1.html', active_tab="Home", active_tab2="LastCheckResults")


@app.route('/settings')
def settings():
    # Add your logic for the settings page
    # Load configuration from JSON file
    with open('config.json', 'r') as file:
        config_data = json.load(file)
        print(f"scheduler configuration:\n${config_data}")

    return render_template('settings.html', config_data=config_data, active_tab="Home", active_tab2="Settings")


@app.route('/login')
def login():
    # Add logic for login
    return "Login page"


@app.route('/logout')
def logout():
    # Add logic for logout
    return "Logout page"


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
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(asyncio.gather(perform_async_task()), timeout=15)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        flash(f'Async Task Completed Successfully at {timestamp}', 'success')
    except concurrent.futures.TimeoutError:
        flash('Asynchronous task timed out!', 'error')
    except Exception as e:
        flash(f'Error: {e}', 'error')

    return redirect(url_for('home'))


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
    print(f"job1: {str(var_one)}, {str(var_two)}")
    print(f"job1: {str(var_one)} + {str(var_two)} = {var_one + var_two}")


def job2(var_one, var_two):
    """Demo job function.

    :param var_one:
    :param var_two:
    """
    with scheduler.app.app_context():
        # print(f"job2: {str(var_one)} + {str(var_two)} = {var_one + var_two}")
        # print(f"job2: {str(var_one)} / {str(0)} = {var_one / 0}")

        import random

        # Generate a random number
        random_number = random.randint(1, 100)  # Adjust the range as needed

        # Check if the random number is odd or even
        if random_number % 2 == 0:
            print(f"{random_number} is an even number.")
            print(f"job2: {str(var_one)} + {str(var_two)} = {var_one + var_two}")
        else:
            print(f"{random_number} is an odd number.")
            print(f"job2: {str(var_one)} / {str(0)} = {var_one / 0}")


scheduler = init_scheduler(app)
logs = init_job_log_store()
init_scheduler_global_state()

if __name__ == '__main__':

    app.run(host=Config.FLASK_RUN_HOST, port=Config.FLASK_RUN_PORT)
    # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass