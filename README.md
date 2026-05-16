# K8s Exam Simulator

A terminal-based CKA/CKAD practice tool with real cluster validation — 30 questions, timed, shuffled, scored.

## Prerequisites

- A Kubernetes cluster (Kind, Minikube, or any cluster with `kubectl` access)
- Python 3.7+ **or** Docker

## Quick Start

### Docker

```bash
docker compose run --rm simulator cka
docker compose run --rm simulator ckad
```

Questions and workspace are baked into the image. To edit questions or keep workspace files on the host:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm simulator cka
```

> **Linux only:** `network_mode: host` lets kubectl inside the container reach `127.0.0.1`
> (where Kind/Minikube listens). On Mac/Windows, remove `network_mode: host` from
> `docker-compose.yml` and point your kubeconfig server to `host.docker.internal`.

### Local Python

```bash
pip3 install pyyaml
bash setup.sh      # checks kubectl, creates workspace/
python3 simulator.py cka
```

## Usage

```bash
python3 simulator.py cka                    # full exam, 120 min, shuffled
python3 simulator.py ckad --questions 5     # quick 5-question session
python3 simulator.py cka --time 45          # 45-minute drill
python3 simulator.py cka --no-shuffle       # questions in filename order
python3 simulator.py validate cka           # score workspace without exam session
python3 simulator.py list cka               # list all available questions
```

### During the exam

Work in a separate terminal — use `kubectl`, `vim`, whatever you need. Come back and enter a command:

| Command | Action |
|---------|--------|
| `n` / `next` | Mark attempted, move on |
| `s` / `skip` | Skip (scores 0) |
| `h` / `hint` | Show detailed hints |
| `t` / `time` | Time remaining |
| `q` / `quit` | Exit early, option to validate |

At the end you'll be prompted to validate. Validation runs `kubectl` against your live cluster and checks YAML files in `./workspace/`.

**Pass threshold: 66%** (same as the real exam).

## Adding Questions

Each question is a standalone JSON file in `questions/cka/` or `questions/ckad/`. Drop a new file in — no other changes needed.

```
questions/
  cka/
    cka-rbac-01.json       ← one question per file
    cka-rbac-02.json       ← add more like this
  ckad/
    ckad-cronjob-01.json
```

### Question format

```json
{
  "id": "cka-rbac-02",
  "weight": 7,
  "task": "Full task description shown during exam...",
  "namespace": "default",
  "hints": ["Shown immediately with the question"],
  "detailed_hints": ["Shown when user types h"],
  "validators": [...]
}
```

### Validator types

**`kubectl`** — runs a command and checks stdout:

```json
{
  "type": "kubectl",
  "description": "Label shown in results",
  "command": "kubectl get deploy myapp -n {namespace} -o jsonpath='{.spec.replicas}'",
  "expected": { "type": "equals", "value": "3" }
}
```

`expected.type` options: `equals`, `contains`, `not_empty`, `exit_code`.
`{namespace}` is replaced with the question's `namespace` field.

**`yaml_file`** — checks a file in `./workspace/`:

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

### Scoring

Each question awards partial credit: `(validators_passed / total) × weight`. Skipped questions score 0.

## Exam tips

```bash
# Speed aliases (set up at the start of the real exam too)
alias k=kubectl
complete -o default -F __start_kubectl k
echo "set nu et ts=2 sw=2" >> ~/.vimrc

# Generate YAML fast
k create deploy app --image=nginx --dry-run=client -o yaml > app.yaml
k run pod --image=nginx --dry-run=client -o yaml > pod.yaml

# Common shortcuts
k expose deploy app --port=80
k set image deploy/app nginx=nginx:1.21
k rollout status deploy/app
k auth can-i create pods --as=system:serviceaccount:ns:sa
```

## Community question sources

- [dgkanatsios/CKAD-exercises](https://github.com/dgkanatsios/CKAD-exercises)
- [David-VTUK/CKA-StudyGuide](https://github.com/David-VTUK/CKA-StudyGuide)
- [killer-sh/cks-cka-ckad-simulator](https://github.com/killer-sh/cks-cka-ckad-simulator)

## Contributing

Add questions as JSON files in `questions/cka/` or `questions/ckad/`. Run `bash test.sh` to validate JSON before submitting a PR.

## License

MIT — see [LICENSE](LICENSE).

---

*Not affiliated with CNCF or Linux Foundation. Questions are community-sourced for educational purposes.*
