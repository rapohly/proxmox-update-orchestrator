#!/usr/bin/env python3

import argparse
import subprocess

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

    elif args.command == "execute":
        print("Executing maintenance plan")


if __name__ == "__main__":
    main()