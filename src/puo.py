#!/usr/bin/env python3

import argparse
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ANSIBLE_DIR = PROJECT_ROOT / "ansible"
PLAYBOOK_DIR = ANSIBLE_DIR / "playbooks"
MIGRATION_PLAN_FILE = PROJECT_ROOT / "runstate" / "migration_plan.json"
LOG_DIR = PROJECT_ROOT / "logs"

def sanitize_group_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", name)

def run_plan(cluster: str, node: str) -> None:
    playbook = PLAYBOOK_DIR / "plan.yml"

    inventory_group = sanitize_group_name(cluster)

    subprocess.run(
        [
            "ansible-playbook",
            str(playbook),
            "-e",
            f"target_cluster={cluster}",
            "-e",
            f"inventory_group={inventory_group}",
            "-e",
            f"update_node={node}",
            "--ask-vault-pass",
        ],
        check=True,
        cwd=ANSIBLE_DIR,
    )

def run_execute(batch_size: int) -> None:
    playbook = PLAYBOOK_DIR / "execute.yml"

    with MIGRATION_PLAN_FILE.open() as f:
        migration_plan = json.load(f)

    target_cluster = migration_plan["target_cluster"]
    inventory_group = sanitize_group_name(target_cluster)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = LOG_DIR / f"puo-{timestamp}.log"

    with log_file.open("w") as log:
        process = subprocess.Popen(
        [
            "ansible-playbook",
            str(playbook),
            "-e",
            f"inventory_group={inventory_group}",
            "-e",
            f"batch_size={batch_size}",
            "--ask-vault-pass",
        ],
        cwd=ANSIBLE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

        for line in process.stdout:
                print(line, end="")
                log.write(line)
                log.flush()

    return_code = process.wait()

    if return_code != 0:
        raise subprocess.CalledProcessError(
            return_code,
            process.args,
        )

    if MIGRATION_PLAN_FILE.exists():
        MIGRATION_PLAN_FILE.unlink()
        
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="puo",
        description="Automated Proxmox cluster maintenance",
        epilog="Written by R. Pohly",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    plan_parser = subparsers.add_parser(
        "plan",
        help="Generate a maintenance plan",
    )

    plan_parser.add_argument(
        "--cluster",
        required=True,
        help="Proxmox cluster name",
    )

    plan_parser.add_argument(
        "--node",
        required=True,
        help="Proxmox node to update",
    )

    exec_parser = subparsers.add_parser(
        "execute",
        help="Execute the current maintenance plan",
    )

    exec_parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        required=False,
        help="Specify how many workloads should migrate simultaneously. Default: 4.",
    )

    args = parser.parse_args()

    if args.command == "plan":
        print(
            f"Planning maintenance for node "
            f"{args.node} in cluster {args.cluster}"
        )
        run_plan(args.cluster, args.node)

    elif args.command == "execute":
        print(f"Executing maintenance plan with batch size {args.batch_size}")
        run_execute(args.batch_size)

if __name__ == "__main__":
    main()