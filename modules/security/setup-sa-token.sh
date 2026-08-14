#!/usr/bin/env bash
set -e

# 1-Year Service Account Token.
#
# This script automates the creation of the Service Account,
# the custom ClusterRole, the Binding, and extracts the 1-year token.
#
# Usage: NAMESPACE=dev-project SA_NAME=os-checker-sa./setup-sa-token.sh
#

# Parameterized Variables with Defaults
NAMESPACE="${NAMESPACE:-default}"
SA_NAME="${SA_NAME:-os-checker-sa}"
ROLE_NAME="os-checker-admin-no-delete"
SECRET_NAME="${SA_NAME}-long-lived-token"

echo "Creating Service Account: ${SA_NAME} in ${NAMESPACE}..."
oc create serviceaccount "${SA_NAME}" -n "${NAMESPACE}" --dry-run=client -o yaml | oc apply -f -

echo "Applying Custom ClusterRole..."
cat <<EOF | oc apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ${ROLE_NAME}
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
- apiGroups: ["security.openshift.io"]
  resources: ["securitycontextconstraints"]
  resourceNames: ["privileged"]
  verbs: ["use"]
EOF

echo "Binding ClusterRole to Service Account..."
cat <<EOF | oc apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: ${ROLE_NAME}-binding-${NAMESPACE}-${SA_NAME}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: ${ROLE_NAME}
subjects:
- kind: ServiceAccount
  name: ${SA_NAME}
  namespace: ${NAMESPACE}
EOF

echo "Requesting 1-Year Token Secret..."
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Secret
type: kubernetes.io/service-account-token
metadata:
  name: ${SECRET_NAME}
  namespace: ${NAMESPACE}
  annotations:
    kubernetes.io/service-account.name: "${SA_NAME}"
EOF

# Wait briefly for the control plane to populate the token data
sleep 2

echo "Extracting Token..."
TOKEN=$(oc get secret "${SECRET_NAME}" -n "${NAMESPACE}" -o jsonpath='{.data.token}' | base64 -d)

echo -e "\n=== SETUP COMPLETE ==="
echo "Token for ${SA_NAME} (Valid for 1 Year):"
echo "${TOKEN}"
echo "======================"
