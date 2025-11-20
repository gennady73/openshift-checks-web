# -*- coding: utf-8 -*-
import os
import mimetypes
from fileinput import filename
from http.client import responses

from cryptography.x509 import OCSPNoCheck
from flask import render_template, abort, jsonify, send_file, g, request, current_app
from .utils import write_file, dir_tree, get_file_extension
from . import blueprint
# OCC
import subprocess

@blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        new_resource_path = request.json.get('dtree')
    else:
        new_resource_path = request.args.get('dtree')
    if new_resource_path is not None:
        g.occode_resource_basepath = f'../openshift-checks/{new_resource_path}'
    resource_basepath = current_app.config.update({'FLASKCODE_RESOURCE_BASEPATH': g.occode_resource_basepath})

    dirname = os.path.basename(g.occode_resource_basepath)
    dtree = dir_tree(g.occode_resource_basepath, g.occode_resource_basepath + '/')

    return render_template('occode/index.html', dirname=dirname, dtree=dtree)

# OCC
# @blueprint.route('/resource-data/<path:file_path>.txt', methods=['GET', 'HEAD'])
@blueprint.route('/resource-data/<path:file_path>', methods=['GET', 'HEAD', 'DELETE'])
def resource_data(file_path):
    abs_file_path = os.path.join(g.occode_resource_basepath, file_path)

    # Basic security: prevent path traversal
    abs_file_path = os.path.abspath(str(abs_file_path))
    if not abs_file_path.startswith(os.path.abspath(g.occode_resource_basepath)):
        abort(403)  # Forbidden

    if not (os.path.exists(abs_file_path) and os.path.isfile(abs_file_path)):
        abort(404)

    if request.method == 'DELETE':
        try:
            os.remove(abs_file_path)
            success = True
            message = "File deleted successfully."
            return '',200 #jsonify({'success': success, 'message': message})
        except Exception as e:
            #return jsonify({"error": str(e)}), 500
            success = False
            message = 'File not deleted'
            return jsonify({'success': success, 'message': message})

    response = send_file(str(os.path.join(g.occode_resource_basepath, file_path)), mimetype='text/plain', max_age=0) # OCC cache_timeout=0
    mimetype, encoding = mimetypes.guess_type(file_path, False)
    if mimetype:
        response.headers.set('X-File-Mimetype', mimetype)
        extension = mimetypes.guess_extension(mimetype, False) or get_file_extension(file_path)
        if extension:
            response.headers.set('X-File-Extension', extension.lower().lstrip('.'))
    if encoding:
        response.headers.set('X-File-Encoding', encoding)
    return response

# OCC
# @blueprint.route('/update-resource-data/<path:file_path>.txt', methods=['POST'])
@blueprint.route('/update-resource-data/<path:file_path>', methods=['POST'])
def update_resource_data(file_path):
    file_path = os.path.join(g.occode_resource_basepath, file_path)
    is_new_resource = bool(int(request.form.get('is_new_resource', 0)))
    if not is_new_resource and not (os.path.exists(file_path) and os.path.isfile(file_path)):
        abort(404)
    success = True
    message = 'File saved successfully'
    resource_data = request.form.get('resource_data', None)
    if resource_data:
        success, message = write_file(resource_data, file_path)
    else:
        success = False
        message = 'File data not uploaded'
    return jsonify({'success': success, 'message': message})

# OCC
@blueprint.route('/execute', methods=['POST'])
#@blueprint.route('/occode/execute', methods=['POST'])
def execute():
    if request.method == 'POST':
        command = request.get_json()['command']
        print(f'### command ###: {command}')
        file_path = request.get_json()['filePath']
        print(f'### file_path ###: {file_path}')

#       USE OF KUBECONFIG
#       1. resolve config file:
#       kubeconfig = f"KUBECONFIG={os.path.expanduser("~/.kube/config")}"
#       2. add following line to the cmd:
#       f"export {kubeconfig} && " \

        if command is None or command == '':
            command = request.json.get('command', '')

        relative_path = "../openshift-checks"
        absolute_path = os.path.abspath(relative_path)
        print(f"working directory : {absolute_path}")
        # cmd = f"cd {absolute_path} && " \
        #       f"source ./venv/bin/activate && " \
        #       f"export INSTALL_CONFIG_PATH={absolute_path}/kubeconfig/install-config.yaml && " \
        #       f"risu.py --list-plugins"
        file_path = os.path.join(g.occode_resource_basepath, file_path)
        is_new_resource = bool(int(request.form.get('is_new_resource', 0)))
        if not is_new_resource and not (os.path.exists(file_path) and os.path.isfile(file_path)):
            cmd = f"cd {absolute_path} && " \
                  f"source ./.venv/bin/activate && " \
                  f"echo Unable to run {file_path}"
        elif command is not None and command != '':
            cmd = f"cd {absolute_path} && " \
                  f"source ./.venv/bin/activate && " \
                  f"{command}"
        else:

            cmd = f"cd {absolute_path} && " \
                  f"source ./.venv/bin/activate && " \
                  f"export INSTALL_CONFIG_PATH={absolute_path}/kubeconfig/install-config.yaml && " \
                  f"./openshift-checks.sh --single {file_path}"

        # print(f"command executed : {cmd}")

        command = cmd

        print(f'### command ###: {command}')
        # Run the command using subprocess
        try:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
            #return render_template('index.html', result=result, command=command)
            resultHTML = render_template('occode/_terminal_output.html', result=result, command=command)
            print(f'### resultHTML ###\n{resultHTML}')
            return resultHTML;
        except subprocess.CalledProcessError as e:
            #return render_template('index.html', result=e.output, command=command, error=True)
            resultHTML = render_template('occode/_terminal_output.html', result=e.output, command=command, error=True)
            print (f'### resultHTML ###\n{resultHTML}')
            return resultHTML;