#!/usr/bin/env python3

import getpass
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

REMOTES_PATH = Path(
    "/etc/proxmox-datacenter-manager/remotes.cfg"
)

INVENTORY_PATH = (
    PROJECT_ROOT
    / "ansible"
    / "inventories"
    / "inventory.json"
)

CLUSTERS_PATH = (
    PROJECT_ROOT
    / "runstate"
    / "clusters.json"
)

GROUP_VARS_PATH = (
    PROJECT_ROOT
    / "ansible"
    / "inventories"
    / "group_vars"
)


def parse_remotes() -> tuple[dict, list[str]]:
    if not REMOTES_PATH.is_file():
        raise FileNotFoundError(
            f"Proxmox remotes file not found: {REMOTES_PATH}"
        )

    inventory = {
        "all": {
            "children": {}
        }
    }

    clusters = []
    current_cluster = None

    lines = REMOTES_PATH.read_text(
        encoding="utf-8"
    ).splitlines()

    for line_number, raw_line in enumerate(lines, start=1):
        stripped_line = raw_line.strip()

        if not stripped_line:
            continue

        if raw_line.startswith("pve:"):
            current_cluster = raw_line.split(":", 1)[1].strip()

            if not current_cluster:
                raise ValueError(
                    f"Missing cluster name on line {line_number}."
                )

            if current_cluster in inventory["all"]["children"]:
                raise ValueError(
                    f"Duplicate cluster '{current_cluster}' "
                    f"on line {line_number}."
                )

            clusters.append(current_cluster)

            inventory["all"]["children"][current_cluster] = {
                "hosts": {}
            }

        elif raw_line.lstrip().startswith("nodes"):
            if current_cluster is None:
                raise ValueError(
                    "Found a nodes entry before a pve cluster "
                    f"declaration on line {line_number}."
                )

            parts = stripped_line.split(None, 1)

            if len(parts) != 2:
                raise ValueError(
                    f"Invalid nodes entry on line {line_number}: "
                    f"{raw_line}"
                )

            node = parts[1].split(",", 1)[0].strip()

            if not node:
                raise ValueError(
                    f"Missing node name on line {line_number}."
                )

            inventory["all"]["children"][current_cluster][
                "hosts"
            ][node] = {}

    if not clusters:
        raise ValueError(
            f"No Proxmox clusters were found in {REMOTES_PATH}."
        )

    return inventory, clusters


def write_json_file(path: Path, data: dict) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")


def prompt_vault_password() -> str:
    print()
    print(
        "Enter the Ansible Vault password that will protect "
        "all cluster credential files."
    )

    vault_password = getpass.getpass(
        "Vault password: "
    )

    vault_password_confirmation = getpass.getpass(
        "Confirm vault password: "
    )

    if not vault_password:
        raise ValueError(
            "Vault password cannot be empty."
        )

    if vault_password != vault_password_confirmation:
        raise ValueError(
            "Vault passwords do not match."
        )

    return vault_password


def create_vault_password_file(
    vault_password: str,
) -> Path:
    file_descriptor, temporary_path = tempfile.mkstemp(
        prefix="proxmox-orchestrator-vault-",
        text=True,
    )

    password_path = Path(temporary_path)

    try:
        os.fchmod(file_descriptor, 0o600)

        with os.fdopen(
            file_descriptor,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(vault_password)
            file.write("\n")

    except Exception:
        password_path.unlink(missing_ok=True)
        raise

    return password_path


def create_cluster_vault(
    cluster: str,
    vault_password_path: Path,
) -> None:
    cluster_vars_path = GROUP_VARS_PATH / cluster
    vault_path = cluster_vars_path / "vault.yml"

    cluster_vars_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    if vault_path.exists():
        print(
            f"Vault already exists for '{cluster}'; skipping."
        )
        return

    print()
    print(f"Configure API credentials for cluster: {cluster}")

    token_id = input(
        "Proxmox API token ID "
        "(example: ansible@pve!orchestrator): "
    ).strip()

    token_secret = getpass.getpass(
        "Proxmox API token secret: "
    ).strip()

    if not token_id:
        raise ValueError(
            f"Token ID cannot be empty for cluster '{cluster}'."
        )

    if not token_secret:
        raise ValueError(
            f"Token secret cannot be empty for cluster '{cluster}'."
        )

    plaintext = (
        f"pve_token_id: {json.dumps(token_id)}\n"
        f"pve_token_secret: "
        f"{json.dumps(token_secret)}\n"
    )

    temporary_plaintext_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f"{cluster}-vault-",
            suffix=".yml",
            delete=False,
        ) as temporary_file:
            temporary_file.write(plaintext)
            temporary_plaintext_path = Path(
                temporary_file.name
            )

        temporary_plaintext_path.chmod(0o600)

        subprocess.run(
            [
                "ansible-vault",
                "encrypt",
                "--vault-password-file",
                str(vault_password_path),
                "--output",
                str(vault_path),
                str(temporary_plaintext_path),
            ],
            check=True,
        )

        vault_path.chmod(0o600)

        print(
            f"Created encrypted vault: {vault_path}"
        )

    finally:
        if temporary_plaintext_path is not None:
            temporary_plaintext_path.unlink(
                missing_ok=True
            )


def create_cluster_vaults(
    clusters: list[str],
) -> None:
    missing_vaults = [
        cluster
        for cluster in clusters
        if not (
            GROUP_VARS_PATH
            / cluster
            / "vault.yml"
        ).exists()
    ]

    if not missing_vaults:
        print()
        print(
            "All discovered clusters already have vault files."
        )
        return

    if shutil.which("ansible-vault") is None:
        raise FileNotFoundError(
            "ansible-vault was not found in PATH."
        )

    vault_password = prompt_vault_password()
    vault_password_path = create_vault_password_file(
        vault_password
    )

    try:
        for cluster in clusters:
            create_cluster_vault(
                cluster,
                vault_password_path,
            )
    finally:
        vault_password_path.unlink(
            missing_ok=True
        )


def main() -> int:
    try:
        inventory, clusters = parse_remotes()

        write_json_file(
            INVENTORY_PATH,
            inventory,
        )

        write_json_file(
            CLUSTERS_PATH,
            {
                "clusters": clusters
            },
        )

        print(
            f"Wrote inventory to {INVENTORY_PATH}"
        )

        print(
            f"Wrote cluster list to {CLUSTERS_PATH}"
        )

        create_cluster_vaults(clusters)

    except (
        FileNotFoundError,
        PermissionError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        print(
            f"Initialization failed: {error}",
            file=sys.stderr,
        )
        return 1

    print()
    print("Initialization complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())