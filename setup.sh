#!/bin/bash
set -e

echo "K8s Exam Simulator — Setup"
echo "==========================="
echo

# Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 not found. Install Python 3.7+."
    exit 1
fi
echo "OK  Python $(python3 --version 2>&1 | awk '{print $2}')"

# pip
if ! command -v pip3 &>/dev/null; then
    echo "ERROR: pip3 not found."
    exit 1
fi

# pyyaml
pip3 install -q pyyaml
echo "OK  pyyaml installed"

# kubectl
if command -v kubectl &>/dev/null; then
    echo "OK  kubectl $(kubectl version --client --short 2>/dev/null | head -1)"
else
    echo "WARN kubectl not found — install before running exams"
    echo "     https://kubernetes.io/docs/tasks/tools/"
fi

# cluster
echo
echo "Checking cluster..."
if kubectl cluster-info &>/dev/null 2>&1; then
    echo "OK  Cluster is reachable"
    kubectl get nodes
else
    echo "WARN No cluster detected. Options:"
    echo
    echo "  Kind (fastest):"
    echo "    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64"
    echo "    chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind"
    echo "    kind create cluster --name cka-practice"
    echo
    echo "  Minikube:"
    echo "    minikube start"
fi

# workspace
mkdir -p workspace
echo
echo "OK  workspace/ ready"

chmod +x simulator.py

echo
echo "==========================="
echo "Setup complete!"
echo
echo "  python3 simulator.py cka"
echo "  python3 simulator.py ckad"
echo "  python3 simulator.py --help"
