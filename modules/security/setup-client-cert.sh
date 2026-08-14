#!/usr/bin/env bash
set -e

#
# Client Certificate (30-Day Limit).
#
# The default OpenShift internal signer (kubernetes.io/kube-apiserver-client) enforces a strict,
# hardcoded maximum validity period of 30 days for client certificates.
# The API server will successfully sign the certificate,
# but it will silently truncate your 1-year request down to 30 days.
#
# Hence, DO NOT try set spec -> expirationSeconds: 31536000 (1 year) in the CSR payload to OpenShift.
#
# Usage: NAMESPACE=dev-project SA_NAME=os-checker-sa./setup-client-cert.sh
#


# Parameterized Variables with Defaults
NAMESPACE="${NAMESPACE:-default}"
SA_NAME="${SA_NAME:-os-checker-sa}"
ROLE_NAME="os-checker-admin-no-delete"
CSR_OBJECT_NAME="csr-${NAMESPACE}-${SA_NAME}"

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

echo "Binding ClusterRole to Service Account Identity..."
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

echo "Generating Private Key and CSR..."
openssl genrsa -out checker.key 2048
openssl req -new -key checker.key -out checker.csr -subj "/CN=system:serviceaccount:${NAMESPACE}:${SA_NAME}/O=system:serviceaccounts:${NAMESPACE}"

echo "Submitting CertificateSigningRequest(CSR) to OpenShift..."
# NOTE: The expirationSeconds below will likely be truncated to 30 days by OpenShift
cat <<EOF | oc apply -f -
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: ${CSR_OBJECT_NAME}
spec:
  request: $(cat checker.csr | base64 | tr -d '\n')
  signerName: kubernetes.io/kube-apiserver-client
  usages:
  - client auth
EOF

echo "Approving CSR..."
oc adm certificate approve "${CSR_OBJECT_NAME}"

echo "Extracting Signed Certificate..."
oc get csr "${CSR_OBJECT_NAME}" -o jsonpath='{.status.certificate}' | base64 -d > checker.crt

echo -e "\n=== SETUP COMPLETE ==="
echo "Files 'checker.key' and 'checker.crt' have been generated."
echo "Use them via: oc get pods --client-certificate=checker.crt --client-key=checker.key"
echo "======================"
