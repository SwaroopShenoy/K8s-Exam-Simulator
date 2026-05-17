#!/usr/bin/env python3
"""K8s Exam Simulator - CKA/CKAD Practice Tool"""

import os
import sys
import json
import yaml
import random
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

PASS_THRESHOLD = 0.66

# Human-readable labels for each capability tag
CAPABILITY_LABELS = {
    "kubeadm":     "kubeadm cluster (/etc/kubernetes/pki/ present)",
    "etcdctl":     "etcdctl binary",
    "helm":        "helm CLI",
    "multi-node":  "cluster with 2+ nodes",
    "gateway-api": "Gateway API CRDs (gateways.gateway.networking.k8s.io)",
}


def _node_count():
    r = subprocess.run(
        "kubectl get nodes --no-headers",
        shell=True, capture_output=True, text=True, timeout=8,
    )
    return len([l for l in r.stdout.strip().splitlines() if l]) if r.returncode == 0 else 0


def detect_capabilities():
    """Return the set of capability tags available in this environment."""
    checks = {
        "kubeadm":     lambda: Path("/etc/kubernetes/pki").exists(),
        "etcdctl":     lambda: subprocess.run("which etcdctl", shell=True, capture_output=True).returncode == 0,
        "helm":        lambda: subprocess.run("which helm", shell=True, capture_output=True).returncode == 0,
        "multi-node":  lambda: _node_count() > 1,
        "gateway-api": lambda: subprocess.run(
            "kubectl get crd gateways.gateway.networking.k8s.io",
            shell=True, capture_output=True, timeout=8,
        ).returncode == 0,
    }
    available = set()
    for cap, check in checks.items():
        try:
            if check():
                available.add(cap)
        except Exception:
            pass
    return available


class ExamSimulator:
    def __init__(self, exam_type, work_dir="./workspace", time_limit_minutes=120,
                 num_questions=None, shuffle=True, ignore_requirements=False):
        self.exam_type = exam_type.upper()
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        self.questions_dir = Path("questions") / exam_type.lower()
        self.time_limit = time_limit_minutes * 60
        self.num_questions = num_questions
        self.shuffle = shuffle
        self.ignore_requirements = ignore_requirements
        self.current_question = 0
        self.start_time = None
        self.answers = {}
        self.capabilities = None  # detected lazily

    def load_questions(self):
        if not self.questions_dir.is_dir():
            print(f"Questions directory not found: {self.questions_dir}")
            print("Make sure you're running from the kubernetes-simulator directory.")
            sys.exit(1)

        files = sorted(self.questions_dir.glob("*.json"))
        if not files:
            print(f"No question files found in {self.questions_dir}")
            sys.exit(1)

        all_questions = []
        for f in files:
            try:
                with open(f) as fp:
                    all_questions.append(json.load(fp))
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: skipping {f.name} — {e}")

        if self.ignore_requirements:
            questions = all_questions
        else:
            if self.capabilities is None:
                self.capabilities = detect_capabilities()
            questions, skipped = [], []
            for q in all_questions:
                missing = [r for r in q.get("requires", []) if r not in self.capabilities]
                if missing:
                    skipped.append((q["id"], missing))
                else:
                    questions.append(q)

            if skipped:
                print(f"\nSkipping {len(skipped)} question(s) — requirements not met in this environment:")
                for qid, missing in skipped:
                    labels = ", ".join(CAPABILITY_LABELS.get(m, m) for m in missing)
                    print(f"  {qid}: needs {labels}")
                print(f"\nRun with --all to include them anyway.\n")

        if self.shuffle:
            random.shuffle(questions)

        if self.num_questions and self.num_questions < len(questions):
            questions = questions[:self.num_questions]

        return questions

    def _run_setup(self, question):
        cmds = question.get("setup", [])
        if not cmds:
            return
        print("  [setup] Preparing environment...", end="", flush=True)
        for cmd in cmds:
            subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
        print(" ready.")

    def clear_screen(self):
        os.system("clear" if os.name != "nt" else "cls")

    def get_time_remaining(self):
        if not self.start_time:
            return self.time_limit
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return max(0, self.time_limit - elapsed)

    def format_time(self, seconds):
        return str(timedelta(seconds=int(seconds)))

    def show_header(self, total):
        remaining = self.get_time_remaining()
        print("=" * 70)
        print(f"  {self.exam_type} EXAM SIMULATOR")
        print(f"  Question {self.current_question + 1}/{total} | Time Remaining: {self.format_time(remaining)}")
        print("=" * 70)
        print()

    def display_question(self, question, total):
        self.clear_screen()
        self.show_header(total)

        print(f"TASK  (Weight: {question['weight']}%)")
        print("-" * 70)
        print(question["task"])
        print()

        if "context" in question:
            print(f"Context: {question['context']}")
            print()

        if "namespace" in question:
            print(f"Namespace: {question['namespace']}")
            print()

        print("HINTS:")
        for hint in question.get("hints", []):
            print(f"  * {hint}")
        print()

        print("-" * 70)
        print(f"Workspace: {self.work_dir.absolute()}")
        print("Commands: [n]ext  [s]kip  [h]int  [t]ime  [q]uit")
        print("-" * 70)

    def run_exam(self):
        print(f"\nDetecting environment capabilities...", end="", flush=True)
        self.capabilities = detect_capabilities()
        caps = ", ".join(sorted(self.capabilities)) or "none"
        print(f" {caps}\n")

        questions = self.load_questions()
        total = len(questions)

        if total == 0:
            print("No questions available for this environment. Run with --all to include all questions.")
            sys.exit(1)

        print(f"Starting {self.exam_type} Exam Simulator")
        print(f"Questions : {total}")
        print(f"Time limit: {self.format_time(self.time_limit)}")
        print(f"Shuffle   : {'yes' if self.shuffle else 'no'}")
        print(f"Workspace : {self.work_dir.absolute()}")
        print("\nPress ENTER to start...")
        input()

        self.start_time = datetime.now()

        for idx, question in enumerate(questions):
            self.current_question = idx

            if self.get_time_remaining() == 0:
                print("\nTime is up!")
                break

            self._run_setup(question)
            self.display_question(question, total)

            while True:
                cmd = input("\n> ").strip().lower()

                if cmd in ("n", "next"):
                    self.answers[idx] = {"question_id": question["id"], "attempted": True, "skipped": False}
                    break

                elif cmd in ("s", "skip"):
                    self.answers[idx] = {"question_id": question["id"], "attempted": False, "skipped": True}
                    break

                elif cmd in ("h", "hint"):
                    hints = question.get("detailed_hints") or question.get("hints", ["Check kubectl docs"])
                    print("\nDetailed hints:")
                    for h in hints:
                        print(f"  * {h}")

                elif cmd in ("t", "time"):
                    print(f"\nTime remaining: {self.format_time(self.get_time_remaining())}")

                elif cmd in ("q", "quit"):
                    print("\nAre you sure you want to quit? (yes/no)")
                    if input("> ").strip().lower() == "yes":
                        self.finish_exam(questions, early_exit=True)
                        return

                else:
                    print("Unknown command. Use: [n]ext  [s]kip  [h]int  [t]ime  [q]uit")

        self.finish_exam(questions)

    def finish_exam(self, questions, early_exit=False):
        self.clear_screen()
        print("\nExam ended early." if early_exit else "\nExam complete!")

        elapsed = (datetime.now() - self.start_time).total_seconds()
        attempted = sum(1 for a in self.answers.values() if a["attempted"])
        skipped = sum(1 for a in self.answers.values() if a["skipped"])
        print(f"\nTime taken : {self.format_time(elapsed)}")
        print(f"Attempted  : {attempted}/{len(questions)}")
        print(f"Skipped    : {skipped}/{len(questions)}")

        print("\n" + "=" * 70)
        print("Validate your solutions? (yes/no)")
        print("This checks YAML files in ./workspace and your cluster resources.")
        print("=" * 70)

        if input("> ").strip().lower() == "yes":
            self.validate_all(questions)
        else:
            print(f"\nValidate later with:  python3 simulator.py validate {self.exam_type.lower()}")

    def validate_all(self, questions):
        print("\n" + "=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)

        total_score = 0
        max_score = sum(q["weight"] for q in questions)

        for idx, question in enumerate(questions):
            if idx not in self.answers or self.answers[idx]["skipped"]:
                print(f"\nQuestion {idx + 1} [{question['id']}]: SKIPPED (0/{question['weight']}%)")
                continue

            print(f"\nQuestion {idx + 1} [{question['id']}]")
            score = self.validate_question(question)
            total_score += score

            status = "PASS" if score == question["weight"] else "PARTIAL" if score > 0 else "FAIL"
            print(f"  => {status} ({score}/{question['weight']}%)")

        pct = (total_score / max_score) * 100 if max_score else 0
        print("\n" + "=" * 70)
        print(f"FINAL SCORE: {total_score}/{max_score}  ({pct:.1f}%)")

        if pct >= PASS_THRESHOLD * 100:
            print("PASS — You passed!")
        else:
            print(f"FAIL — Need {PASS_THRESHOLD * 100:.0f}% to pass. Keep practicing!")
        print("=" * 70)

    def validate_question(self, question):
        validators = question.get("validators", [])
        if not validators:
            return 0

        passed = sum(1 for v in validators if self.run_validator(v, question))
        return round((passed / len(validators)) * question["weight"], 2)

    def run_validator(self, validator, question):
        vtype = validator["type"]
        try:
            if vtype == "kubectl":
                return self._validate_kubectl(validator, question)
            elif vtype == "yaml_file":
                return self._validate_yaml_file(validator, question)
            else:
                print(f"  [?] Unknown validator type: {vtype}")
                return False
        except Exception as e:
            print(f"  [!] Validation error: {e}")
            return False

    def _validate_kubectl(self, validator, question):
        cmd = validator["command"].replace("{namespace}", question.get("namespace", "default"))
        expected = validator["expected"]

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            output = result.stdout.strip()

            check_type = expected.get("type", "contains")
            check_value = expected.get("value", "")

            if check_type == "contains":
                ok = check_value in output
            elif check_type == "equals":
                ok = output == check_value
            elif check_type == "not_empty":
                ok = len(output) > 0
            elif check_type == "exit_code":
                ok = result.returncode == check_value
            else:
                ok = False

            label = validator.get("description", cmd)
            mark = "[+]" if ok else "[-]"
            print(f"  {mark} {label}")
            if not ok and validator.get("show_output"):
                print(f"      got: {output!r}")
            return ok

        except subprocess.TimeoutExpired:
            print(f"  [-] Timeout: {cmd}")
            return False

    def _validate_yaml_file(self, validator, question):
        filepath = self.work_dir / validator["filename"]
        if not filepath.exists():
            print(f"  [-] File not found: {validator['filename']}")
            return False

        try:
            with open(filepath) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"  [-] Invalid YAML in {validator['filename']}: {e}")
            return False

        for field_path, expected_value in validator.get("required_fields", {}).items():
            actual = self._get_nested(data, field_path)
            if actual != expected_value:
                print(f"  [-] {field_path}: expected {expected_value!r}, got {actual!r}")
                return False

        print(f"  [+] {validator['filename']} is valid")
        return True

    @staticmethod
    def _get_nested(data, path):
        value = data
        for key in path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value


def list_questions(exam_type, capabilities=None, show_all=False):
    questions_dir = Path("questions") / exam_type.lower()
    files = sorted(questions_dir.glob("*.json"))
    if not files:
        print(f"No questions found in {questions_dir}")
        return

    available, skipped = [], []
    for f in files:
        try:
            q = json.loads(f.read_text())
            reqs = q.get("requires", [])
            missing = [r for r in reqs if capabilities and r not in capabilities] if not show_all else []
            if missing:
                skipped.append((q, missing))
            else:
                available.append(q)
        except Exception as e:
            print(f"  {f.name} — ERROR: {e}")

    total = len(available) + len(skipped)
    print(f"\n{exam_type.upper()} Questions — {len(available)}/{total} available in this environment\n")

    for q in available:
        reqs = f"  [{', '.join(q['requires'])}]" if q.get("requires") else ""
        setup = "  [has setup]" if q.get("setup") else ""
        print(f"  {q['id']:38s}  weight={q['weight']:2d}{reqs}{setup}")

    if skipped:
        print(f"\n  -- Skipped (run with --all to include) --")
        for q, missing in skipped:
            labels = ", ".join(CAPABILITY_LABELS.get(m, m) for m in missing)
            print(f"  {q['id']:38s}  weight={q['weight']:2d}  (needs: {labels})")

    total_weight = sum(q["weight"] for q in available)
    print(f"\nAvailable weight: {total_weight}%")


def main():
    parser = argparse.ArgumentParser(
        description="K8s Exam Simulator — CKA/CKAD Practice Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 simulator.py cka                     # Full CKA exam (120 min, shuffled)
  python3 simulator.py ckad --questions 5      # Quick 5-question session
  python3 simulator.py cka --time 30           # 30-minute timed drill
  python3 simulator.py cka --no-shuffle        # Questions in file order
  python3 simulator.py cka --all               # Include questions needing kubeadm/helm/etc.
  python3 simulator.py validate cka            # Validate workspace against cluster
  python3 simulator.py list cka                # List available questions for this environment
  python3 simulator.py list cka --all          # List all questions including skipped ones
        """,
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    exam_parent = argparse.ArgumentParser(add_help=False)
    exam_parent.add_argument("--time", "-t", type=int, default=120, metavar="MINUTES",
                             help="time limit in minutes (default: 120)")
    exam_parent.add_argument("--questions", "-q", type=int, default=None, metavar="N",
                             help="number of questions to draw (default: all)")
    exam_parent.add_argument("--no-shuffle", dest="shuffle", action="store_false",
                             help="keep questions in file order (default: shuffle)")
    exam_parent.add_argument("--workspace", default="./workspace", metavar="DIR",
                             help="workspace directory for YAML files (default: ./workspace)")
    exam_parent.add_argument("--all", dest="ignore_requirements", action="store_true",
                             help="include questions even if their requirements aren't detected")
    exam_parent.set_defaults(shuffle=True, ignore_requirements=False)

    subparsers.add_parser("cka", parents=[exam_parent], help="Start CKA exam")
    subparsers.add_parser("ckad", parents=[exam_parent], help="Start CKAD exam")

    p_val = subparsers.add_parser("validate", help="Validate workspace + cluster without running exam")
    p_val.add_argument("exam_type", choices=["cka", "ckad"])
    p_val.add_argument("--workspace", default="./workspace", metavar="DIR")
    p_val.add_argument("--all", dest="ignore_requirements", action="store_true")

    p_list = subparsers.add_parser("list", help="List available questions for an exam")
    p_list.add_argument("exam_type", choices=["cka", "ckad"])
    p_list.add_argument("--all", dest="show_all", action="store_true",
                        help="show all questions including those with unmet requirements")

    args = parser.parse_args()

    if args.command in ("cka", "ckad"):
        sim = ExamSimulator(
            exam_type=args.command,
            work_dir=args.workspace,
            time_limit_minutes=args.time,
            num_questions=args.questions,
            shuffle=args.shuffle,
            ignore_requirements=args.ignore_requirements,
        )
        sim.run_exam()

    elif args.command == "validate":
        sim = ExamSimulator(
            exam_type=args.exam_type,
            work_dir=args.workspace,
            ignore_requirements=args.ignore_requirements,
        )
        questions = sim.load_questions()
        sim.answers = {i: {"question_id": q["id"], "attempted": True, "skipped": False}
                       for i, q in enumerate(questions)}
        sim.validate_all(questions)

    elif args.command == "list":
        caps = None if args.show_all else detect_capabilities()
        list_questions(args.exam_type, capabilities=caps, show_all=args.show_all)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
