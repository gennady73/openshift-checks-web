import deepdiff.helper
from deepdiff import DeepDiff
from deepdiff.helper import SetOrdered
from typing import Any
import json
import os
import time
from urllib.parse import unquote
from flask import Blueprint, render_template, jsonify, flash, url_for, redirect, request
from flask import Flask, session, get_flashed_messages
import asyncio
import concurrent.futures
from datetime import datetime
from pathlib import Path
import re


app:Flask

diff_blueprint: Blueprint = Blueprint('diff', __name__, template_folder='templates/diff')

CHECK_RESULT_DIR_NAME = 'results' # in future releases, this value must be retrieved from the app config.

# The default name pattern of "result" file: <YYYYMMDD>-<HHMMSS>-<CLUSTER_ID>-<CLUSTER_NAME>.json
RESULT_DIR_REGEX_PATTERN = r"([\d]{8}-[\d]{6})(-)[0-9]+(-)([\w\d\-]+)(.json)"

DIFF_RESULT_DIR_NAME = 'diffs' # in future releases, this value must be retrieved from the app config.
# The default name pattern of "result" file:
# <YYYYMMDD>-<HHMMSS>-<CLUSTER_ID>-<CLUSTER_NAME>_to_<YYYYMMDD>-<HHMMSS>-<CLUSTER_ID>-<CLUSTER_NAME>_diff.json
DIFF_RESULT_DIR_REGEX_PATTERN = (r"([\d]{8}-[\d]{6})(-)[0-9]+(-)([\w\d\-]+)"
                                 r"(_to_)"
                                 r"([\d]{8}-[\d]{6})(-)[0-9]+(-)([\w\d\-]+)"
                                 r"(_diff.json)")

STATIC_DATA_BLUEPRINT:Blueprint|None = None
CHECK_RESULT_PATH: str|None = None
DIFF_RESULT_PATH:str|None = None

RESULT_DIR_REGEX = re.compile(RESULT_DIR_REGEX_PATTERN)
DIFF_RESULT_DIR_REGEX = re.compile(DIFF_RESULT_DIR_REGEX_PATTERN)

class OscDiffOperator:
    def __init__(self, include_paths):
        self.include_paths = include_paths

    def match(self, level) -> bool:
        return True #isinstance(level.t1, dict) and isinstance(level.t2, dict)

    def give_up_diffing(self, level, diff_instance) -> bool:
        #return level.path() not in self.include_paths
        # print(f"TYPE T1 ({level.t1}) : {type(level.t1)}")
        # print(f"TYPE T2 ({level.t2}) : {type(level.t2)}")
        #
        result = False
        if isinstance(level.t1, dict) and isinstance(level.t2, dict):
            r1:dict = level.t1

            r2:dict = level.t2
            #
            # return True if((r1.get("result") is not None and r2.get("result") is not None) and level.t1.result == level.t2.result) else False

            result = (r1.get("result") is not None and r2.get("result") is not None) and set(level.t1.get('result')) == set(level.t2.get('result'))

            if level.path() not in self.include_paths:
                result = False

            id = "aab5df6bea597b656cc0d45e57655643b134c14c36175cd217d05e3597159cdc78a37d55d1537aed86d969314b587655a1894cccc52c7602e3902d4822ce43d5"
            id_new="076e3e203099eb19bf0e85a904a9976e02f37bc0c47a7b286fec10ccb9f23f2c1c618c5ee6193c9215fa05553a3319e9d50177c8c331a44b57329a036cc625b1"
            if(id == r1.get("id")):
                print(f"*** CHANGED ***:\n {level.t1.get('id')}")
            if(result):
                print(f"*** CHANGED ***:\n {level.t2.get('result')}")

            if(id_new == r1.get("id")):
                print(f"*** NEW ***:\n {level.t1.get('id')}")
            if(result):
                print(f"*** NEW ***:\n {level.t2.get('result')}")

        return result #level.path() not in self.include_paths

    @classmethod
    def _remove_pattern(cls, t: str):
        return t # re.sub(cls._pattern, cls._substitute, t)

    def normalize_value_for_hashing(self, parent: Any, obj: Any) -> Any:
        """
        Used for ignore_order=True
        """
        if isinstance(obj, str):
            return obj # self._remove_pattern(obj)
        return obj

def init_diff(app_flask: Flask):
    global app
    app = app_flask

    global STATIC_DATA_BLUEPRINT
    STATIC_DATA_BLUEPRINT = app.blueprints.get('static_data_blueprint')

    global CHECK_RESULT_PATH
    CHECK_RESULT_PATH = os.path.join(os.path.abspath(STATIC_DATA_BLUEPRINT.static_folder), CHECK_RESULT_DIR_NAME)

    global DIFF_RESULT_PATH
    DIFF_RESULT_PATH = os.path.join(os.path.abspath(STATIC_DATA_BLUEPRINT.static_folder), DIFF_RESULT_DIR_NAME)

    print(f"CHECK_RESULT_PATH={CHECK_RESULT_PATH}")
    print(f"DIFF_RESULT_PATH={DIFF_RESULT_PATH}")

def clear_messages():
    if session is not None:
        session.pop('_flashes', None)

#  OLD VERSION
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

# OLD VERSION - WITHOUT A BASELINE
# def json_files_list(directory: str, pattern: str | None = None, start_date=None, end_date=None) -> list:
#     if pattern is None or pattern.strip() == '':
#         pattern = RESULT_DIR_REGEX_PATTERN
#     regex = re.compile(pattern)
#
#     matched_file_names = []
#
#     for f in os.listdir(directory):
#         if not f.endswith('.json'):
#             continue
#
#         match = regex.match(f)
#         if match:
#             # Extract the timestamp group (e.g., '20260326-101026')
#             timestamp_str = match.group(1)
#             file_dt = datetime.strptime(timestamp_str, "%Y%m%d-%H%M%S")
#
#             # Apply time boundaries if they were passed in the request
#             if start_date and file_dt < start_date:
#                 continue
#             if end_date and file_dt > end_date:
#                 continue
#
#             path = Path(os.path.join(directory, f))
#             matched_file_names.append(path.name)
#
#     # Sort descending (newest first)
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


@diff_blueprint.route('/monaco-editor/<path:subpath>', methods=['GET'])
def monaco_editor(subpath):
    #http: // localhost: 5500 / local - web - resources / fonts.googleapis.com / css?family = Overpass
    #if str(subpath).find('google',0)>=0:
    print(f"subpath={subpath}")
    ru = request.url.replace('diff/', 'occode/static/vendor/') # occode/static/vendor/monaco-editor
    return redirect(unquote(ru))


@diff_blueprint.route('/local-web-resources/<path:subpath>', methods=['GET'])
def local_web_resources(subpath):
    #http: // localhost: 5500 / local - web - resources / fonts.googleapis.com / css?family = Overpass
    if str(subpath).find('google',0)>=0:
        print(f"subpath={subpath}")
    ru = request.url.replace('diff/', '')
    return redirect(unquote(ru))

# OLD VERSION
# @diff_blueprint.route('/data/list/from', methods=['GET'])
# def check_result_data_list_from():
#     json_files_list_from = json_files_list(directory=CHECK_RESULT_PATH, pattern=RESULT_DIR_REGEX_PATTERN)
#     return jsonify(json_files_list_from)

@diff_blueprint.route('/data/list/from', methods=['GET'])
def check_result_data_list_from():
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')

    # Parse the strings sent from the frontend AJAX call
    start_date = datetime.strptime(start_str, "%Y%m%d-%H%M%S") if start_str else None
    end_date = datetime.strptime(end_str, "%Y%m%d-%H%M%S") if end_str else None

    filtered_files = json_files_list(
        directory=CHECK_RESULT_PATH,
        pattern=RESULT_DIR_REGEX_PATTERN,
        start_date=start_date,
        end_date=end_date
    )

    return jsonify(filtered_files)

# OLD VERSION
# @diff_blueprint.route('/data/list/to', methods=['GET'])
# def check_result_data_list_to():
#     json_files_list_to = json_files_list(directory=CHECK_RESULT_PATH, pattern=RESULT_DIR_REGEX_PATTERN)
#     return jsonify(json_files_list_to)

@diff_blueprint.route('/data/list/to', methods=['GET'])
def check_result_data_list_to():
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')

    # Parse the strings sent from the frontend AJAX call
    start_date = datetime.strptime(start_str, "%Y%m%d-%H%M%S") if start_str else None
    end_date = datetime.strptime(end_str, "%Y%m%d-%H%M%S") if end_str else None

    filtered_files = json_files_list(
        directory=CHECK_RESULT_PATH,
        pattern=RESULT_DIR_REGEX_PATTERN,
        start_date=start_date,
        end_date=end_date
    )

    return jsonify(filtered_files)


@diff_blueprint.route('/data/list', methods=['GET'])
def diff_result_data_list():
    json_diff_list = json_files_list(directory=DIFF_RESULT_PATH, pattern=DIFF_RESULT_DIR_REGEX_PATTERN)
    return jsonify(json_diff_list)

@diff_blueprint.route('/data/selected', methods=['GET'])
def diff_result_file_name():
    result_file_name = session.get('selected_diff_result', 'osc.json')
    return jsonify(result_file_name)

@diff_blueprint.route('/', methods=['GET', 'POST'])
def diff_home():
    # static_ext1_blueprint = app.blueprints.get('static_ext1_blueprint')
    # list_json_from = json_files_list(directory=static_ext1_blueprint.static_folder, pattern=RESULT_DIR_REGEX_PATTERN)
    # list_json_to = json_files_list(directory=static_ext1_blueprint.static_folder, pattern=RESULT_DIR_REGEX_PATTERN)
    # json_diff_list = json_files_list(directory=static_ext1_blueprint.static_folder, pattern=DIFF_RESULT_DIR_REGEX_PATTERN)

    list_json_from = json_files_list(directory=CHECK_RESULT_PATH, pattern=RESULT_DIR_REGEX_PATTERN)
    list_json_to = json_files_list(directory=CHECK_RESULT_PATH, pattern=RESULT_DIR_REGEX_PATTERN)
    json_diff_list = json_files_list(directory=DIFF_RESULT_PATH, pattern=DIFF_RESULT_DIR_REGEX_PATTERN)

    qs = request.query_string.decode()
    if request.method == 'GET' and request.args.get('json'):
        selected_diff_result = request.args.get('json')
        regex = re.compile(DIFF_RESULT_DIR_REGEX_PATTERN)
        if regex.match(selected_diff_result):
            selected_from_to = selected_diff_result.replace('_diff.json','').split('_to_')
            if len(selected_from_to) == 2:
                session['selected_diff_result'] = selected_diff_result
                session['selected_check_result_from'] = f"{selected_from_to[0]}.json"
                session['selected_check_result_to'] =  f"{selected_from_to[1]}.json"

    result_file_name = session.get('selected_diff_result', 'osc.json') # osc.json - empty diff report
    selected_check_result_from = session.get('selected_check_result_from', None)
    selected_check_result_to = session.get('selected_check_result_to', None)

    # Renders the Diff page (which is almost a clone of Home)
    return render_template('diff/diff.html',
                           cluster_info_list=app.cluster_info_list,
                           selected_cluster=session.get('selected_cluster','0'),
                           active_tab="Diff", active_tab2="LastDiffResults",
                           check_results_from_list=list_json_from,
                           check_results_to_list=list_json_to,
                           jsonDiffFile=result_file_name,
                           list_json = json_diff_list,
                           selected_check_result_from=selected_check_result_from,
                           selected_check_result_to=selected_check_result_to)


#@diff_blueprint.route('/snapshot_diff.json', methods=['GET'])
#@diff_blueprint.route('/osc.json', methods=['GET'])
@diff_blueprint.route('/<filename>.json', methods=['GET'])
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

    if json_file_name.endswith('_diff.json') and DIFF_RESULT_DIR_REGEX.match(json_file_name):
        directory = DIFF_RESULT_PATH
    elif (not json_file_name.endswith('_diff.json') and RESULT_DIR_REGEX.match(json_file_name)) or json_file_name == 'osc.json':
        directory = CHECK_RESULT_PATH
    else:
        return 404

    json_file_path = os.path.join(directory, f"{json_file_name}")

    try:
        # Open the file and load the data into a Python dictionary/list
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        # Return the Python object as a JSON response
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Data file not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Error decoding JSON"}), 500

# not in use
# @diff_blueprint.route('/get_diff_data')
# def get_diff_data():
#     """Reads two snapshot JSONs, calculates the delta, and returns the hydration payload."""
#     try:
#         # 1. Read the JSON files (Replace paths with your actual JSON paths)
#         with open('snapshot_1.json', 'r') as f1, open('snapshot_2.json', 'r') as f2:
#             snap1 = json.load(f1)
#             snap2 = json.load(f2)
#     except FileNotFoundError:
#         return jsonify()
#
#     # 2. Convert lists to dictionaries indexed by the unique check ID
#     # (e.g., "CMD-OC-1")
#     # 2. Extract the 'results' array and convert to dictionaries indexed by 'id'
#     results1 = snap1 #snap1.get("results", )
#     results2 = snap2 #snap2.get("results", )
#
#     dict1 = results1 #{item[1].get('id'): item[1] for item in results1.items() if 'id' in item[1]}
#     dict2 = results2 #{item[1].get('id'): item[1] for item in results2.items() if 'id' in item[1]}
#
#     # 3. Calculate differences ignoring order
#     # diff = DeepDiff(dict1, dict2, ignore_order=True)
#     diff = DeepDiff(dict1, dict2, ignore_order=True,
#     custom_operators = [
#         MyOperator(include_paths="root['results'][1].get('id').items()")
#         ]
#     )
#
#     comparison_data = {
#         "metadata": results2.get("metadata"),
#         "results": {}
#     }
#
#     # 4. Hydrate the new payload with state_change properties
#
#     # Safely extract the results dictionary to allow for easy old_value lookups
#     old_results = dict1.get('results', {})
#     new_results = dict2.get('results', {})
#
#     # Define what return codes are considered healthy/neutral based on RISU mappings
#     # 0 = Okay, 40 = Info, 66 = Skipped
#     healthy_rcs = {}
#
#     for check_id, check_data in new_results.items():
#         diff_item = dict()
#         diff_item[check_id] = check_data
#         dia:SetOrdered = diff['dictionary_item_added']
#         for j in dia:
#             print(f"dia: {j}")
#
#         id_new = "076e3e203099eb19bf0e85a904a9976e02f37bc0c47a7b286fec10ccb9f23f2c1c618c5ee6193c9215fa05553a3319e9d50177c8c331a44b57329a036cc625b1"
#         id_new_2 = "b3aa39686528a337147297c461f4bd37fcb784aa100f284ba1f868365fbbd3dfde2de858d4b98ad9442fae13c11e04b76d675039ed626e64582c9bb626a78fd1"
#
#         if check_id == id_new or check_id == id_new_2:
#             print("NEW")
#
#         # 1. Check if this item is completely new in snapshot 2
#         # ["root['results']['076e3e203099eb19bf0e85a904a9976e02f37bc0c47a7b286fec10ccb9f23f2c1c618c5ee6193c9215fa05553a3319e9d50177c8c331a44b57329a036cc625b1']"]
#         # is_new = 'dictionary_item_added' in diff and any(f"root['results']['{check_id}']") and check_id not in diff['dictionary_item_added']
#         is_new = 'dictionary_item_added' in diff and any(f"['{check_id}']" in k for k in diff['dictionary_item_added'])
#         if is_new:
#             diff_item[check_id]['state_change'] = 'new'
#
#         # 2. Check if existing values changed inside this check
#         elif 'values_changed' in diff or 'type_changes' in diff:
#             changed_keys = []
#
#             for k in diff['values_changed'].keys():
#                 print(f"key: {k}")
#
#             print(f"""key: root['results']['{check_id}']['result']['err']""")
#             if check_id == "aab5df6bea597b656cc0d45e57655643b134c14c36175cd217d05e3597159cdc78a37d55d1537aed86d969314b587655a1894cccc52c7602e3902d4822ce43d5":
#                 print("UPDATE changed keys")
#
#             if 'values_changed' in diff:
#                 changed_keys.extend([k for k in diff['values_changed'].keys() if f"""root['results']['{check_id}']['result']['err']""" in k])
#             if 'type_changes' in diff:
#                 changed_keys.extend([k for k in diff['type_changes'].keys() if f"root['results']['{check_id}']['result']['err']" in k])
#
#             # Filter out volatile keys we want to ignore for visual diffing (like execution time)
#             significant_keys = [k for k in changed_keys if not k.endswith("['time']")]
#
#             if not significant_keys:
#                 # Only the time changed, so visually it is unchanged
#                 diff_item[check_id]['state_change'] = 'unchanged'
#             else:
#                 # 3. Retrieve the old and new Return Code (RC)
#                 old_rc = old_results.get(check_id, {}).get('result', {}).get('rc', -1)
#                 new_rc = diff_item.get(check_id, {}).get('result', {}).get('rc', -1)
#
#                 if old_rc != new_rc:
#                     # The RC changed: check if it crossed the boundary between healthy and degraded
#                     if new_rc not in healthy_rcs and old_rc in healthy_rcs:
#                         diff_item[check_id]['state_change'] = 'degraded'
#                     elif new_rc in healthy_rcs and old_rc not in healthy_rcs:
#                         diff_item[check_id]['state_change'] = 'resolved'
#                     else:
#                         # RC changed, but stayed within the same category (e.g., Warning to the Failed)
#                         diff_item[check_id]['state_change'] = 'changed'
#                 else:
#                     # The RC is identical (e.g. 40), but output/err strings changed
#                     # Example: 'Total nodes: 1' -> 'Total nodes: 10'
#                     diff_item[check_id]['state_change'] = 'changed'
#         else:
#             diff_item[check_id]['state_change'] = 'unchanged'
#
#         comparison_data.get("results").update(diff_item)
#
#     id_removed = "eff1bd6e029612c1b95c39b4636c2bbc548a09296306a1c353b70b70666379add092fe13a3e169b90cf504884f9d3a630ac019a051d7f6b9c7ad0675f095c5cd"
#
#     # 5. Handle items that were removed in snapshot 2
#     if 'dictionary_item_removed' in diff:
#         import re
#         for removed_key in diff['dictionary_item_removed']:
#             match = re.search(r"(root\[['\"]results['\"]\])\['(.*?)'\]", removed_key)
#             if match:
#                 check_id = match.group(2)
#                 # Ensure we only grab it if it's the actual check ID, not a sub-property
#                 if check_id in old_results:
#                     removed_item = dict()
#                     removed_item[check_id] = dict(old_results[check_id])
#                     removed_item[check_id]['state_change'] = 'removed'
#                     comparison_data.get("results").update(removed_item)
#
#
#
#     return comparison_data  #jsonify(comparison_data)

async def async_get_diff_data(cluster_name:str, diff_from:str, diff_to:str, timestamp:str):
    """Reads two snapshot JSONs, calculates the delta, and returns the hydration payload."""

    try:
        # 1. Read the JSON files (Replace paths with your actual JSON paths)
        with open(diff_from, 'r') as f1, open(diff_to, 'r') as f2:
            snap1 = json.load(f1)
            snap2 = json.load(f2)
    except FileNotFoundError as error:
        return jsonify({'diff_process_error': f'{error}'})

    # 2. Convert lists to dictionaries indexed by the unique check ID
    # (e.g., "CMD-OC-1")
    # 2. Extract the 'results' array and convert to dictionaries indexed by 'id'
    results1 = snap1 #snap1.get("results", )
    results2 = snap2 #snap2.get("results", )

    dict1 = results1 #{item[1].get('id'): item[1] for item in results1.items() if 'id' in item[1]}
    dict2 = results2 #{item[1].get('id'): item[1] for item in results2.items() if 'id' in item[1]}
    try:
        # 3. Calculate differences ignoring order
        # diff = DeepDiff(dict1, dict2, ignore_order=True)
        diff = DeepDiff(dict1, dict2, ignore_order=True,
        custom_operators = [
            OscDiffOperator(include_paths="root['results'][1].get('id').items()")
            ]
        )

        comparison_data = {
            "metadata": results2.get("metadata"),
            "results": {}
        }

        # 4. Hydrate the new payload with state_change properties

        # Safely extract the results dictionary to allow for easy old_value lookups
        old_results = dict1.get('results', {})
        new_results = dict2.get('results', {})

        # Define what return codes are considered healthy/neutral based on RISU mappings
        # 0 = Okay, 40 = Info, 66 = Skipped
        healthy_rcs = {}

        for check_id, check_data in new_results.items():
            diff_item = dict()
            diff_item[check_id] = check_data
            dia:SetOrdered = diff.get('dictionary_item_added',[])
            for j in dia:
                print(f"dia: {j}")

            id_new = "076e3e203099eb19bf0e85a904a9976e02f37bc0c47a7b286fec10ccb9f23f2c1c618c5ee6193c9215fa05553a3319e9d50177c8c331a44b57329a036cc625b1"
            id_new_2 = "b3aa39686528a337147297c461f4bd37fcb784aa100f284ba1f868365fbbd3dfde2de858d4b98ad9442fae13c11e04b76d675039ed626e64582c9bb626a78fd1"

            if check_id == id_new or check_id == id_new_2:
                print("NEW")

            # 1. Check if this item is completely new in snapshot 2
            # ["root['results']['076e3e203099eb19bf0e85a904a9976e02f37bc0c47a7b286fec10ccb9f23f2c1c618c5ee6193c9215fa05553a3319e9d50177c8c331a44b57329a036cc625b1']"]
            # is_new = 'dictionary_item_added' in diff and any(f"root['results']['{check_id}']") and check_id not in diff['dictionary_item_added']
            is_new = 'dictionary_item_added' in diff and any(f"['{check_id}']" in k for k in diff.get('dictionary_item_added',[]))
            if is_new:
                diff_item[check_id]['state_change'] = 'new'

            # 2. Check if existing values changed inside this check
            elif 'values_changed' in diff or 'type_changes' in diff:
                changed_keys = []

                # for k in diff['values_changed'].keys():
                #     print(f"key: {k}")

                print(f"""key: root['results']['{check_id}']['result']['err']""")
                if check_id == "aab5df6bea597b656cc0d45e57655643b134c14c36175cd217d05e3597159cdc78a37d55d1537aed86d969314b587655a1894cccc52c7602e3902d4822ce43d5":
                    print("UPDATE changed keys")

                if 'values_changed' in diff:
                    changed_keys.extend([k for k in diff['values_changed'].keys() if f"""root['results']['{check_id}']['result']['err']""" in k])
                if 'type_changes' in diff:
                    changed_keys.extend([k for k in diff['type_changes'].keys() if f"root['results']['{check_id}']['result']['err']" in k])

                # Filter out volatile keys we want to ignore for visual diffing (like execution time)
                significant_keys = [k for k in changed_keys if not k.endswith("['time']")]

                if not significant_keys:
                    # Only the time changed, so visually it is unchanged
                    diff_item[check_id]['state_change'] = 'unchanged'
                else:
                    # 3. Retrieve the old and new Return Code (RC)
                    old_rc = old_results.get(check_id, {}).get('result', {}).get('rc', -1)
                    new_rc = diff_item.get(check_id, {}).get('result', {}).get('rc', -1)

                    old_value = diff["values_changed"][f"root['results']['{check_id}']['result']['err']"]['old_value']

                    if old_rc != new_rc:
                        # The RC changed: check if it crossed the boundary between healthy and degraded
                        if new_rc not in healthy_rcs and old_rc in healthy_rcs:
                            diff_item[check_id]['state_change'] = 'degraded'
                        elif new_rc in healthy_rcs and old_rc not in healthy_rcs:
                            diff_item[check_id]['state_change'] = 'resolved'
                        else:
                            # RC changed, but stayed within the same category (e.g., Warning to the Failed)
                            diff_item[check_id]['state_change'] = 'changed'
                    else:
                        # The RC is identical (e.g. 40), but output/err strings changed
                        # Example: 'Total nodes: 1' -> 'Total nodes: 10'
                        diff_item[check_id]['state_change'] = 'changed'

                    if old_value:
                        if check_id == "aab5df6bea597b656cc0d45e57655643b134c14c36175cd217d05e3597159cdc78a37d55d1537aed86d969314b587655a1894cccc52c7602e3902d4822ce43d5":
                            print("UPDATE changed keys")
                        old_out = old_results.get(check_id, {}).get('result', {}).get('out', '')
                        old_err = old_results.get(check_id, {}).get('result', {}).get('err', '')
                        print(f"--- OLD VALUE OUT  : {check_id} ---\n{old_out}")
                        print(f"--- OLD VALUE ERR  : {check_id} ---\n{old_err}")
                        print(f"--- OLD VALUE DIFF : {check_id} ---\n{old_value}")
                        diff_item[check_id]['old_result'] = old_value
            else:
                diff_item[check_id]['state_change'] = 'unchanged'

            comparison_data.get("results").update(diff_item)

        id_removed = "eff1bd6e029612c1b95c39b4636c2bbc548a09296306a1c353b70b70666379add092fe13a3e169b90cf504884f9d3a630ac019a051d7f6b9c7ad0675f095c5cd"

        # 5. Handle items that were removed in snapshot 2
        if 'dictionary_item_removed' in diff:
            import re
            for removed_key in diff['dictionary_item_removed']:
                match = re.search(r"(root\[['\"]results['\"]\])\['(.*?)'\]", removed_key)
                if match:
                    check_id = match.group(2)
                    # Ensure we only grab it if it's the actual check ID, not a sub-property
                    if check_id in old_results:
                        removed_item = dict()
                        removed_item[check_id] = dict(old_results[check_id])
                        removed_item[check_id]['state_change'] = 'removed'
                        comparison_data.get("results").update(removed_item)
    except Exception as error:
        return jsonify({'diff_process_error': f'{error}'})

    return comparison_data  #jsonify(comparison_data)


@diff_blueprint.route('/async-task', methods=['POST'])
async def async_task_route():

    result_file_name=None
    json_diff_list =[]
    diff_from = None
    diff_to = None
    request_json = request.get_json()
    list_json_from = []
    list_json_to = []
    output = {}

    try:
        cluster_id = request_json['cluster_id']                     # or from selected_cluster=session.get('selected_cluster','0')
        cluster_name = request_json['cluster_name']
        diff_from = request_json['check_results_from']              # 'snapshot_1.json'
        diff_to = request_json['check_results_to']                  # 'snapshot_2.json'
        selected_diff = session.get('selected_diff_result', None)   # 'snapshot_diff.json' request_json['selected_diff_result'] or from

        list_json_from = json_files_list(directory=CHECK_RESULT_PATH, pattern=RESULT_DIR_REGEX_PATTERN)
        list_json_to = json_files_list(directory=CHECK_RESULT_PATH, pattern=RESULT_DIR_REGEX_PATTERN)
        json_diff_list = json_files_list(directory=DIFF_RESULT_PATH, pattern=DIFF_RESULT_DIR_REGEX_PATTERN)

        # just a mock
        diff_attributes = {
            "diff_from": "",
            "diff_to": "",
            "cluster_id": "",
            "cluster_name": "",
            "success": "ready"
        }

        if (diff_from is None or not diff_from.strip()) and (diff_to is None or not diff_to.strip()):
            diff_attributes.pop("success")
            diff_attributes.update({"error": "Nothing to compare, select values 'From' and 'To' in order to proceed."})
        elif diff_from is None or not diff_from.strip():
            diff_attributes.pop("success")
            diff_attributes.update({"error": "Nothing to compare, select value 'From' in order to proceed."})
        elif diff_to is None or not diff_to.strip():
            diff_attributes.pop("success")
            diff_attributes.update({"error": "Nothing to compare, select value 'To' in order to proceed."})


        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        diff_readiness = (diff_attributes.get('error', '')).strip('\n')

        if len(diff_readiness):
            flash(f'Task execution failed at {timestamp}. {diff_readiness}', 'error')

            result_file_name = 'osc.json'
            json_diff_list = ['osc.json']
            selected_check_result_from =  'osc.json'
            selected_check_result_to =  'osc.json'
        else:
            result = await asyncio.wait_for(asyncio.gather(
                async_get_diff_data(cluster_name=cluster_id,
                                    diff_from=os.path.join(CHECK_RESULT_PATH, diff_from),
                                    diff_to=os.path.join(CHECK_RESULT_PATH, diff_to),
                                    timestamp=timestamp)),
                timeout=600)

            if len(result) > 0:
                output = result[0]
                if type(output) == dict and 'diff_process_error' not in output and 'metadata' in output and 'results' in output:
                    flash(f'Task execution is scheduled at {timestamp}.', 'success')
                    result_file_name = f"{diff_from.replace('.json', '')}_to_{diff_to.replace('.json', '')}_diff.json"

                    with open(os.path.join(DIFF_RESULT_PATH, result_file_name),
                              "w") as json_diff_file:
                        json.dump(output, json_diff_file, indent=4)

                    session['selected_diff_result'] = result_file_name

                elif output.is_json and 'diff_process_error' in output.get_json().keys():
                    diff_process_error = output.get_json()['diff_process_error']
                    clear_messages()
                    flash(f'Task execution failed at {timestamp}. {diff_process_error}', 'error')

                else:
                    diff_process_error = "The diff data has not a valid structure."
                    print(f"ERROR: {diff_process_error}")
                    clear_messages()
                    flash(f'Task execution failed at {timestamp}. {diff_process_error}', 'error')

            session['selected_check_result_from'] = diff_from
            session['selected_check_result_to'] = diff_to

    except concurrent.futures.TimeoutError:
        flash('Task timed out!', 'error')
    except Exception as e:
        flash(f'Task Error: {e}', 'error')

    return jsonify({
        "diff_tab_nav": render_template('partials/diff/tab_nav.html',
                                        cluster_info_list=app.cluster_info_list,
                                        selected_cluster=session.get('selected_cluster', '0'),
                                        active_tab="Diff", active_tab2="LastDiffResults",
                                        check_results_from_list=list_json_from,
                                        check_results_to_list=list_json_to,
                                        jsonDiffFile=result_file_name,
                                        list_json=json_diff_list,
                                        selected_check_result_from=diff_from,
                                        selected_check_result_to=diff_to,
                                        ),


        "result_container": render_template('diff-result.html',
                                            cluster_info_list=app.cluster_info_list,
                                            selected_cluster=session.get('selected_cluster', '0'),
                                            check_results_from_list=list_json_from,
                                            check_results_to_list=list_json_to,
                                            jsonDiffFile=result_file_name,
                                            list_json=json_diff_list,
                                            selected_check_result_from=diff_from,
                                            selected_check_result_to=diff_to),
        "notification": get_flashed_messages(True),
        "json_diff_list": json_diff_list,
        "json_diff_file": result_file_name,
        "data": output
    })

if __name__ == '__main__':
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    json_diff = async_get_diff_data(diff_from='snapshot_1.json',diff_to='snapshot_2.json',cluster_name='', timestamp=timestamp)
    with open("snapshot_diff.json", "w") as json_file:
        json.dump(json_diff, json_file, indent=4)