# async_task.py

import asyncio
import subprocess
import os
import sys
import logging

import app
from modules.security import extract_login_command, oc_login2

def get_data_from_db():
    try:
        relative_path = "../openshift-checks"
        absolute_path = os.path.abspath(relative_path)
        logging.getLogger('apscheduler').info(f"The working directory: {absolute_path}")
        ##      f"oc login -u kubeadmin -p admin https://api.crc.testing:6443 && " \
        # cmd = f"cd {absolute_path} && " \
        #       f"source ./venv/bin/activate && " \
        #       f"export INSTALL_CONFIG_PATH={absolute_path}/kubeconfig/install-config.yaml && " \
        #       f"oc login --token sha256~Eg_PJIpYRRMSlWbiF3lvxgdWrbn0Oiof3mKWc22beII https://api.gu-ocp-sno-lab.rh-igc.com:6443 " \
        #        f"--insecure-skip-tls-verify=true && " \
        #       f"risu.py -l"
        login_attributes = extract_login_command('/home/gunger/Documents/IGC_LAB/kubeconfig')
        login_cmd = login_attributes['command']
        cmd = f"cd {absolute_path} && " \
              f"export RISU_BASE={absolute_path} && " \
              f"source ./.venv/bin/activate && " \
              f"export INSTALL_CONFIG_PATH={absolute_path}/kubeconfig/install-config.yaml && " \
              f"{login_cmd} && " \
              f"risu.py -l"

        logging.getLogger('apscheduler').info(f"The command prepared to execute : '{cmd}'")

        p = subprocess.Popen(
            [cmd],
            cwd=absolute_path,
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        output, error = p.communicate()

        if error:
            print('The command execution error:', error, file=sys.stderr)
            logging.getLogger('apscheduler').info(f"The command execution error : {error}")
        else:
            logging.getLogger('apscheduler').error(f"The command execution success : {output}")

        return output
    except subprocess.CalledProcessError as e:
        # Handle any errors that occur while running the script
        error_message = f"Error: {e.stderr.strip()}"
        return error_message
    except Exception as e:
        # Handle other exceptions, if any
        return f"Error: {str(e)}"


async def perform_async_task():
    # Simulate a long-running asynchronous task
    # await asyncio.sleep(5)
    logging.getLogger('apscheduler').debug(f"get_data_from_db task begin.")
    result = get_data_from_db()
    logging.getLogger('apscheduler').debug(f"get_data_from_db task result={result}")
    # return "Task completed successfully"


async def perform_async_task_2(name: str, login_attributes: None):
    # Simulate a long-running asynchronous task
    # await asyncio.sleep(5)
    logging.getLogger('apscheduler').debug(f"get_data_from_cluster task begin.")
    result = get_data_from_cluster(name, login_attributes)
    logging.getLogger('apscheduler').debug(f"get_data_from_cluster task result={result}")
    # return "Task completed successfully"
    return result

def get_data_from_cluster(cluster_name: str, login_attributes: None):
    try:
        relative_path = "../openshift-checks"
        absolute_path = os.path.abspath(relative_path)
        logging.getLogger('apscheduler').info(f"The working directory: {absolute_path}")
        ##      f"oc login -u kubeadmin -p admin https://api.crc.testing:6443 && " \
        # cmd = f"cd {absolute_path} && " \
        #       f"source ./venv/bin/activate && " \
        #       f"export INSTALL_CONFIG_PATH={absolute_path}/kubeconfig/install-config.yaml && " \
        #       f"oc login --token sha256~Eg_PJIpYRRMSlWbiF3lvxgdWrbn0Oiof3mKWc22beII https://api.gu-ocp-sno-lab.rh-igc.com:6443 " \
        #        f"--insecure-skip-tls-verify=true && " \
        #       f"risu.py -l"
        if not login_attributes:
            login_attributes = extract_login_command(cluster_name)

        login_cmd = login_attributes['command']
        cmd = f"cd {absolute_path} && " \
              f"source ./.venv/bin/activate && " \
              f"export INSTALL_CONFIG_PATH={absolute_path}/kubeconfig/install-config.yaml && " \
              f"{login_cmd} && " \
              f"risu.py -l"

        logging.getLogger('apscheduler').info(f"The command prepared to execute : '{cmd}'")

        p = subprocess.Popen(
            [cmd],
            cwd=absolute_path,
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        output, error = p.communicate()

        if error:
            print('The command execution error:', error, file=sys.stderr)
            logging.getLogger('apscheduler').info(f"The command execution error : {error}")
        else:
            logging.getLogger('apscheduler').error(f"The command execution success : {output}")

        return output
    except subprocess.CalledProcessError as e:
        # Handle any errors that occur while running the script
        error_message = f"Error: {e.stderr.strip()}"
        return error_message
    except Exception as e:
        # Handle other exceptions, if any
        return f"Error: {str(e)}"