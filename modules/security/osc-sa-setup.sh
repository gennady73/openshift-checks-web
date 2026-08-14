#!/usr/bin/env bash
# Apply The Core RBAC Configuration allow to the "OpenShit Checks" to operate against the cluster.

SERVICE_ACCOUNT="os-checker-sa"
NAMESPACE="default"

# Create a custom ClusterRole that explicitly grants all verbs except delete,
# while specifically allowing the use verb on the privileged Security Context Constraint (SCC) so oc debug node works.
oc apply -f ./osc-cluster-role.yaml

# Create the Service Account:
oc create serviceaccount $SERVICE_ACCOUNT -n $NAMESPACE

# Bind the Custom Role to the Service Account:
oc adm policy add-cluster-role-to-user os-checker-admin-no-delete -z $SERVICE_ACCOUNT -n $NAMESPACE

# Create the Long-Lived Token Secret:
 oc apply -f ./osc-sa-secret.yaml

 # Extract the Token for use:
 oc get secret "$SERVICE_ACCOUNT-token" -n $NAMESPACE -o jsonpath='{.data.token}' | base64 -d
