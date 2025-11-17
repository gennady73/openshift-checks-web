from flask import Blueprint, render_template, Flask
#import flaskcode
import  sys
import os
import modules.occode as occode

app:Flask=None

editor_blueprint: Blueprint = Blueprint('editor', __name__, static_folder='static', template_folder='templates/editor')
flaskcode_blueprint: Blueprint = occode.blueprint
occode_blueprint: Blueprint = occode.blueprint

def init_code_editor(app_flask: Flask):
    global app
    app = app_flask
    # openshift-checks/checks-extended
    app.config.from_object(occode.default_config)
    app.config['FLASKCODE_APP_TITLE'] = 'OpenShift Checks'
    app.config['FLASKCODE_EDITOR_THEME'] = 'vs'
    app.config['FLASKCODE_RESOURCE_BASEPATH'] = os.path.abspath('../openshift-checks/checks-extended')
    # flaskcode.blueprint.defaultLang = 'shell'
    # app.register_blueprint(flaskcode.blueprint, url_prefix='/flaskcode')
    # app.register_blueprint(editor_blueprint, url_prefix='/editor')
    occode.config = app.config

# @flaskcode_blueprint.route('/flackcode', methods=['GET', 'POST'])
# def flaskcode_home():
#     return render_template('flaskcode', active_tab="EditorR", active_tab2="JobList")


# @editor_blueprint.route('/', methods=['GET', 'POST'])
# def code_editor_home():
#     return render_template('editor/editor.html', active_tab="EditorR", active_tab2="JobList")

from modules.occode import views
import os
import mimetypes
from fileinput import filename

from cryptography.x509 import OCSPNoCheck
from flask import render_template, abort, jsonify, send_file, g, request, current_app
from modules.occode.utils import write_file, dir_tree, get_file_extension


@editor_blueprint.route('/', methods=['GET', 'POST'])
def code_editor_home():
    if request.method == 'POST':
        new_resource_path = request.json.get('dtree')
    else:
        new_resource_path = request.args.get('dtree')
    if new_resource_path is not None:
        g.occode_resource_basepath = f'../openshift-checks/{new_resource_path}'
    else:
        g.occode_resource_basepath = current_app.config.get('FLASKCODE_RESOURCE_BASEPATH')

    resource_basepath = current_app.config.update({'FLASKCODE_RESOURCE_BASEPATH': g.occode_resource_basepath})

    dirname = os.path.basename(g.occode_resource_basepath)
    dtree = dir_tree(g.occode_resource_basepath, g.occode_resource_basepath + '/')
    #return render_template('flaskcode/index.html', dirname=dirname, dtree=dtree)
    # return render_template('editor/editor.html', active_tab="EditorR", active_tab2="JobList", dirname=dirname, dtree=dtree)
    return render_template( 'editor/editor.html', active_tab="EditorR", active_tab2="JobList",
                            dirname=dirname,
                            dtree=dtree,
                            clusters=app.clusters)
