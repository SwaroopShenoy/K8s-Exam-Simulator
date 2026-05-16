#!/bin/bash
echo "K8s Exam Simulator — Tests"
echo "==========================="
echo
PASS=0; FAIL=0

check() {
    local label="$1"; shift
    if "$@" &>/dev/null; then
        echo "PASS  $label"
        ((PASS++))
    else
        echo "FAIL  $label"
        ((FAIL++))
    fi
}

# Python
check "Python 3 available" python3 --version

# pyyaml
check "PyYAML importable" python3 -c "import yaml"

# simulator
check "simulator.py is executable" test -x simulator.py

# question files
cka_count=$(ls questions/cka/*.json 2>/dev/null | wc -l)
ckad_count=$(ls questions/ckad/*.json 2>/dev/null | wc -l)
check "CKA questions present ($cka_count files)"  test "$cka_count" -gt 0
check "CKAD questions present ($ckad_count files)" test "$ckad_count" -gt 0

# valid JSON
all_ok=true
for f in questions/cka/*.json questions/ckad/*.json; do
    python3 -m json.tool "$f" &>/dev/null || { echo "FAIL  Invalid JSON: $f"; all_ok=false; ((FAIL++)); }
done
$all_ok && { echo "PASS  All question files are valid JSON"; ((PASS++)); }

# list command
check "simulator list cka works" python3 simulator.py list cka

# workspace
mkdir -p workspace
check "workspace/ exists" test -d workspace

# kubectl (optional)
echo
if command -v kubectl &>/dev/null; then
    echo "INFO  kubectl found"
    if kubectl cluster-info &>/dev/null 2>&1; then
        echo "INFO  Cluster reachable — validate commands will work"
    else
        echo "WARN  kubectl found but no cluster detected"
    fi
else
    echo "WARN  kubectl not found — needed for exam validation"
fi

echo
echo "==========================="
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && echo "All good! Run: python3 simulator.py cka" || exit 1
