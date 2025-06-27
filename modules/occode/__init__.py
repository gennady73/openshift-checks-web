"""occode Flask Blueprint"""
import os
from flask import Blueprint, current_app, g, abort
from . import default_config

blueprint = Blueprint(
    'occode',
    __name__,
    static_folder='static',
    template_folder='templates/occode'
)

config = default_config

@blueprint.url_value_preprocessor
def manipulate_url_values(endpoint, values):
    if endpoint != 'occode.static':
        resource_basepath = current_app.config.get('FLASKCODE_RESOURCE_BASEPATH')
        if not (resource_basepath and os.path.isdir(resource_basepath)):
            abort(500, '`FLASKCODE_RESOURCE_BASEPATH` is not a valid directory path')
        else:
            g.occode_resource_basepath = os.path.abspath(resource_basepath).rstrip('/\\')
    else:
        return 'static'

@blueprint.context_processor
def process_template_context():
    return dict(
        # app_version=__version__,
        app_title=current_app.config.get('FLASKCODE_APP_TITLE', default_config.FLASKCODE_APP_TITLE),
        editor_theme=current_app.config.get('FLASKCODE_EDITOR_THEME', default_config.FLASKCODE_EDITOR_THEME),
    )

from . import views

__all__ = ["views", "blueprint", "default_config", "cli", "utils"]

