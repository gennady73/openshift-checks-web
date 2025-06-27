import os
import json

class Config:
    # Other configuration settings...
    FLASK_RUN_HOST = os.getenv('FLASK_RUN_HOST', default='localhost')
    FLASK_RUN_PORT = os.getenv('FLASK_RUN_PORT', default='5500')
    SERVER_NAME = f"{FLASK_RUN_HOST}:{FLASK_RUN_PORT}"

    DEBUG = True
    # Add the path to the external template folder
    TEMPLATE_FOLDER = '../openshift-checks'

    # css and js
    STATIC_FOLDER = '../openshift-checks/local-web-resources'
    # async
    SESSION_TYPE = 'filesystem'

    # occode
    FLASKCODE_APP_TITLE = 'FlaskCode'
    FLASKCODE_EDITOR_THEME = 'vs-dark'
    FLASKCODE_RESOURCE_BASEPATH = None
