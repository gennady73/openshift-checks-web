import os
import yaml
import logging
import subprocess
import shlex

from jobstores.sqlalchemy import ClusterCredentialStore
from models import ClusterCredential

LOGGER = logging.getLogger("security")

def extract_username(user_entry: str) -> str:
    # For example: "kube:admin/api-cluster:6443" => "kube:admin"
    return user_entry.split("/")[0] if "/" in user_entry else user_entry

def get_kubeconfigs() -> list:
    """
    Returns a list of kubeconfig file paths from the KUBECONFIG env variable.
    Expands ~ if present in any path.
    """
    raw_kubeconfig = os.environ.get("KUBECONFIG", os.path.expanduser("~/.kube/config"))
    kubeconfigs = [os.path.expanduser(path) for path in raw_kubeconfig.split(":")]
    LOGGER.debug(f"Resolved kubeconfig paths: {kubeconfigs}")
    return kubeconfigs

def extract_login_command(cluster_name: str) -> dict:
    """
    Extracts login command using token and server for the specified cluster name.

    Args:
        cluster_name (str): Name of the OpenShift cluster (as defined in kubeconfig).

    Returns:
        dict: Contains the constructed login command and metadata.
    """
    for kc_path in get_kubeconfigs():
        LOGGER.debug(f"Inspecting kubeconfig: {kc_path}")
        try:
            with open(kc_path, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            LOGGER.warning(f"Skipping invalid kubeconfig {kc_path}: {e}")
            continue

        clusters = {c['name']: c['cluster'] for c in config.get('clusters', [])}
        if cluster_name not in clusters:
            LOGGER.debug(f"Cluster '{cluster_name}' not found in {kc_path}")
            continue

        cluster = clusters[cluster_name]
        contexts = config.get('contexts', [])
        users = {u['name']: u['user'] for u in config.get('users', [])}

        matched_context = next(
            (ctx for ctx in contexts if ctx['context']['cluster'] == cluster_name),
            None
        )
        if not matched_context:
            LOGGER.debug(f"No matching context found for cluster '{cluster_name}' in {kc_path}")
            continue

        context_name = matched_context['name']
        context = matched_context['context']
        user_name = context['user']
        user = users.get(user_name, {})

        token = user.get('token')
        if not token:
            LOGGER.error(f"No token found for user '{user_name}' in {kc_path}")
            raise ValueError(f"No token found for user '{user_name}' in kubeconfig")

        server = cluster['server']
        insecure = cluster.get("insecure-skip-tls-verify", False)

        cmd = ["oc", "login", f"--token={token}", f"--server={server}"]
        if insecure:
            cmd.append("--insecure-skip-tls-verify=true")

        LOGGER.debug(f"Login command constructed for cluster '{cluster_name}': {' '.join(cmd)}")

        return {
            "command": ' '.join(cmd),
            "user": extract_username(user_name),
            "cluster": cluster_name,
            "context": context_name,
            "kubeconfig": kc_path
        }

    LOGGER.error(f"Cluster '{cluster_name}' not found in any kubeconfig")
    raise ValueError(f"Cluster '{cluster_name}' not found in any kubeconfig")


def oc_login2(cluster_name: str, credentials_store:ClusterCredentialStore):
    credentials:ClusterCredential = credentials_store.get_credential(credential_id=cluster_name)

    cmd = ["oc", "login", f"--token={credentials.token}", f"--server={credentials.server}"]
    if credentials.insecure:
        cmd.append("--insecure-skip-tls-verify=true")

    LOGGER.debug(f"Login command constructed for cluster '{cluster_name}': {' '.join(cmd)}")

    return {
        "command": ' '.join(cmd),
        "user": credentials.user,
        "cluster": credentials.name,
        "context": credentials.namespace,
        "kubeconfig": ''
    }

def oc_login(cluster_name: str):
    """
    Attempts to log into the specified OpenShift cluster using the token extracted from kubeconfig.

    Args:
        cluster_name (str): The name of the cluster selected from the UI.

    Returns:
        dict: Result containing login status or error message.
    """
    try:
        login_attributes = extract_login_command(cluster_name)
        login_cmd = shlex.split(login_attributes['command'])  # Safely split string to list
        LOGGER.debug(f"Attempting login with command: {' '.join(login_cmd)}")

        subprocess.run(login_cmd, check=True, capture_output=True, text=True)
        LOGGER.info(f"Login to OpenShift cluster successful: {cluster_name}")

        return {
            "status": "success",
            "selected": cluster_name,
            "user": login_attributes.get("user"),
            "context": login_attributes.get("context")
        }

    except subprocess.CalledProcessError as e:
        LOGGER.error(f"Login failed for cluster {cluster_name}: {e.stderr or str(e)}")
        return {"error": e.stderr or str(e)}

    except Exception as e:
        LOGGER.error(f"Unexpected error during login to {cluster_name}: {str(e)}")
        return {"error": str(e)}
