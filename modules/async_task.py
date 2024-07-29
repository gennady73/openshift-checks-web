# async_task.py

import asyncio
import subprocess
import os
import sys


def get_data_from_db():
    try:
        relative_path = "../openshift-checks"
        absolute_path = os.path.abspath(relative_path)
        print(f"working directory : {absolute_path}")

        cmd = f"cd {absolute_path} && " \
              f"source .venv/bin/activate && " \
              f"export INSTALL_CONFIG_PATH={absolute_path}/kubeconfig/install-config.yaml && " \
              f"oc login -u kubeadmin -p Kn3dq-J96ZJ-d2jQT-9QkJH https://api.crc.testing:6443 && " \
              f"risu.py -l"
        print(f"command executed : {cmd}")

        p = subprocess.Popen(
            [cmd],
            cwd=absolute_path,
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        output, error = p.communicate()

        print(output)
        if error:
            print('error:', error, file=sys.stderr)

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
    print(f">>>> get_data_from_db")
    result = get_data_from_db()
    print(f">>>> result={result}")
    # return "Task completed successfully"

