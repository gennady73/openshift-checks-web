#!/usr/bin/env bash
# Generates a Certificate Signing Request (CSR) with a specific user and group,
# have OpenShift sign it, and then bind your RBAC role to that user.

# Note:
# By default, OpenShift 4 heavily restricts the maximum validity of CSRs generated through the internal API to 30 days.
# When requesting a 1-year client certificate, it is often better to sign the CSR using your own corporate CA and
# add that CA to the OpenShift API trust bundle.

# Using the Certificate:
# The key and certificate(e.g. 'checker.crt' and 'checker.key') are must be mounted on the filesystem,
# in order tomake the underlying 'oc' commands able to use them instead of a token, as following:
# oc get pods --client-certificate=/path/to/checker.crt --client-key=/path/to/checker.key
#

SERVICE_ACCOUNT="os-checker-sa"
NAMESPACE="default"

# Create a custom ClusterRole that explicitly grants all verbs except delete,
# while specifically allowing the use verb on the privileged Security Context Constraint (SCC) so oc debug node works.
oc apply -f ./osc-cluster-role.yaml

# Generate a Private Key and CSR:
# Set the Common Name (CN) to checker-user and the Organization (O) to 'system:masters' (or a custom group).
openssl genrsa -out checker.key 2048
# openssl req -new -key checker.key -out checker.csr -subj "/CN=checker-user/O=checker-group"
openssl req -new -key checker.key -out checker.csr -subj \
  "/CN=system:serviceaccount:$NAMESPACE:$SERVICE_ACCOUNT/O=system:serviceaccounts:$NAMESPACE"

# Submit the CSR to OpenShift:
# Request 1 year (31536000 seconds), but be aware the API server may truncate this.
cat <<EOF | oc apply -f -
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: checker-user-csr
spec:
  request: $(cat checker.csr | base64 | tr -d '\n')
  signerName: kubernetes.io/kube-apiserver-client
  expirationSeconds: 31536000
  usages:
  - client auth
EOF

# Approve the CSR:
oc adm certificate approve checker-user-csr

# Extract the Signed Certificate:
oc get csr checker-user-csr -o jsonpath='{.status.certificate}' | base64 -d > checker.crt

# Bind the Custom Role to the Certificate's User:
oc adm policy add-cluster-role-to-user os-checker-admin-no-delete checker-user
