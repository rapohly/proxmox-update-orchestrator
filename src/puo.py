#!/usr/bin/env python3

import argparse
import subprocess
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ANSIBLE_DIR = PROJECT_ROOT / "ansible"
PLAYBOOK_DIR = ANSIBLE_DIR / "playbooks"
RUNSTATE_DIR = PROJECT_ROOT / "runstate"
CLI_STATE_FILE = RUNSTATE_DIR / "cli_state.json"

def run_plan(cluster: str, node: str) -> None:
    playbook = PLAYBOOK_DIR / "plan.yml"
    subprocess.run(
        [
            "ansible-playbook",
            str(playbook),
            "-e",
            f"target_cluster={cluster}",
            "-e",
            f"update_node={node}",
            "--ask-vault-pass",
        ],
        check=True,
        cwd=ANSIBLE_DIR,
    )

    RUNSTATE_DIR.mkdir(exist_ok=True)

    with CLI_STATE_FILE.open("w") as f:
        json.dump(
            {
                "target_cluster": cluster,
                "update_node": node,
            },
            f,
            indent=2,
        )

def run_execute() -> None:
    playbook = PLAYBOOK_DIR / "execute.yml"

    with CLI_STATE_FILE.open() as f:
        state = json.load(f)

    target_cluster = state["target_cluster"]

    subprocess.run(
        [
            "ansible-playbook",
            str(playbook),
            "-e",
            f"target_cluster={target_cluster}",
            "--ask-vault-pass",
        ],
        check=True,
        cwd=ANSIBLE_DIR,
    )

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

    subparsers.add_parser(
        "execute",
        help="Execute the current maintenance plan",
    )

    args = parser.parse_args()

    if args.command == "plan":
        print(
            f"Planning maintenance for node "
            f"{args.node} in cluster {args.cluster}"
        )
        run_plan(args.cluster, args.node)

    elif args.command == "execute":
        print("Executing maintenance plan")
        run_execute()


if __name__ == "__main__":
    main()