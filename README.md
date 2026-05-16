# K8s Exam Simulator - CKA/CKAD Practice Tool

Simple, extensible Kubernetes exam simulator with real cluster validation.

## Features

✅ **Real exam format** - Questions presented one by one with timer  
✅ **Auto-validation** - Checks your cluster resources and YAML files  
✅ **Extensible** - Easy to add your own questions  
✅ **Free** - Uses real questions from community repos  
✅ **Offline** - Works completely locally  

## Prerequisites

1. **Kubernetes cluster** (one of):
   - Kind (recommended)
   - Minikube
   - kubeadm cluster
   - Any K8s cluster with kubectl access

2. **Python 3.7+**

3. **kubectl** configured

## Quick Start

### Option A: Docker (no local Python/kubectl needed)

```bash
# Build and run (interactive terminal)
docker compose run --rm simulator cka

# With custom options
docker compose run --rm simulator cka --questions 3 --time 30
docker compose run --rm simulator ckad --no-shuffle
docker compose run --rm simulator list cka

# Validate only (no exam session)
docker compose run --rm simulator validate cka
```

> **Linux only:** `network_mode: host` in `docker-compose.yml` lets kubectl inside the
> container reach a Kind/minikube cluster on `127.0.0.1`. On Mac/Windows, edit
> `docker-compose.yml` to remove `network_mode: host` and update your kubeconfig server
> address to use `host.docker.internal` instead of `127.0.0.1`.

Your `./workspace` and `./questions` directories are mounted into the container, so YAML
files and question edits persist and take effect without rebuilding the image.

---

### Option B: Local Python

### 1. Setup Cluster (if you don't have one)

#### Option A: Kind (Fastest)
```bash
# Install Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Create cluster
kind create cluster --name cka-practice

# Verify
kubectl cluster-info
kubectl get nodes
```

#### Option B: Minikube
```bash
# Install
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start
minikube start

# Verify
kubectl get nodes
```

### 2. Install Dependencies

```bash
pip3 install pyyaml
```

### 3. Run Simulator

#### CKA Exam
```bash
python3 simulator.py cka
```

#### CKAD Exam
```bash
python3 simulator.py ckad
```

## How to Use

### During Exam

1. **Read the question** carefully
2. **Work in ./workspace** directory for YAML files
3. **Use kubectl** directly on your cluster
4. **Commands available**:
   - `n` or `next` - Move to next question (marks as attempted)
   - `s` or `skip` - Skip question
   - `h` or `hint` - Show additional hints
   - `t` or `time` - Check remaining time
   - `q` or `quit` - Exit exam

### Example Workflow

```bash
# Start exam
python3 simulator.py cka

# Question appears, you work on it:
cd workspace

# Create YAML
kubectl create deployment web --image=nginx --dry-run=client -o yaml > web-deploy.yaml

# Edit as needed
vim web-deploy.yaml

# Apply
kubectl apply -f web-deploy.yaml

# Verify
kubectl get deploy web

# Move to next question
# Type: n

# At the end, validate all
# The simulator will check:
# - YAML files in ./workspace
# - Resources in your cluster
```

### Validation Only

If you finished the exam and want to validate later:

```bash
python3 simulator.py validate cka
# or
python3 simulator.py validate ckad
```

## Adding Your Own Questions

Questions are stored in JSON format in `questions/<exam>/questions.json`

### Question Format

```json
{
  "id": "unique-id",
  "weight": 7,
  "task": "Question text with requirements...",
  "namespace": "default",
  "hints": ["Hint 1", "Hint 2"],
  "detailed_hints": ["More detailed hint"],
  "validators": [
    {
      "type": "kubectl",
      "description": "What this checks",
      "command": "kubectl get pod mypod -o jsonpath='{.status.phase}'",
      "expected": {
        "type": "equals",
        "value": "Running"
      }
    }
  ]
}
```

### Validator Types

#### kubectl validator
Runs kubectl command and checks output:

```json
{
  "type": "kubectl",
  "command": "kubectl get deploy myapp -n {namespace} -o jsonpath='{.spec.replicas}'",
  "expected": {
    "type": "equals",  // or "contains", "not_empty", "exit_code"
    "value": "3"
  }
}
```

#### yaml_file validator
Checks YAML file structure:

```json
{
  "type": "yaml_file",
  "filename": "deploy.yaml",
  "required_fields": {
    "kind": "Deployment",
    "metadata.name": "myapp",
    "spec.replicas": 3
  }
}
```

## Importing Questions from GitHub

### From killer.sh repo

```bash
# Clone
git clone https://github.com/killer-sh/cks-cka-ckad-simulator.git

# Their questions are in simulator/cka.md and simulator/ckad.md
# Convert them to JSON format and add to questions/cka/questions.json
```

### Community Repos

- **David-VTUK CKA**: https://github.com/David-VTUK/CKA-StudyGuide
- **Dimitris-iliadis**: https://github.com/dimitris-iliadis/cka-practice-environment
- **dgkanatsios CKAD**: https://github.com/dgkanatsios/CKAD-exercises

## Tips for Real Exam

### Setup (Do this in exam first 2 minutes)

```bash
# Aliases
alias k=kubectl
complete -o default -F __start_kubectl k

# vim config
echo "set nu et ts=2 sw=2" >> ~/.vimrc

# Test
k get nodes
```

### Time Management

- 2 hours = 120 minutes
- ~15-20 questions
- 6-8 minutes per question average
- Do easy ones first!
- Leave 10-15 min for review

### Speed Techniques

```bash
# Generate YAML fast
k create deploy app --image=nginx --dry-run=client -o yaml > app.yaml

# Quick edits
k edit deploy app

# Set resources
k set resources deploy app --requests=cpu=100m,memory=128Mi

# Expose service
k expose deploy app --port=80
```

## Customization

### Change Time Limit

Edit `simulator.py`:
```python
self.time_limit = 7200  # seconds (2 hours)
```

### Add More Questions

1. Edit `questions/cka/questions.json` or `questions/ckad/questions.json`
2. Add new question object
3. Run simulator

### Custom Validators

Add new validator types in `run_validator()` method:
```python
elif validator_type == 'custom':
    return self.validate_custom(validator, question)
```

## Troubleshooting

### "Questions file not found"
- Make sure you're in the k8s-exam-simulator directory
- Check questions/cka/questions.json exists

### "kubectl command failed"
- Verify cluster is running: `kubectl get nodes`
- Check context: `kubectl config current-context`

### "YAML validation failed"
- Check file is in ./workspace directory
- Verify YAML syntax: `cat workspace/file.yaml`

## Score Interpretation

- **66%+** - PASS (same as real exam)
- **75%+** - Good
- **85%+** - Excellent
- **95%+** - Ready for exam!

## Contributing

Add questions by editing JSON files in `questions/` directory.

## License

MIT - Free to use and modify

## Disclaimer

This is a practice tool, not affiliated with CNCF or Linux Foundation.
Questions are community-sourced for educational purposes.

---

**Good luck with your exam preparation!** 🚀

Remember: Practice makes perfect. The more you use this simulator, the faster you'll get!
