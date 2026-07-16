#!/usr/bin/env python3

import json
from pathlib import Path 

inventory_path = (
    Path(__file__).resolve().parent.parent
    / "ansible"
    / "inventories"
    / "inventory.json"
)

inventory_path.parent.mkdir(parents=True, exist_ok=True)

inventory = {
    "all": {
        "children": {}
    }
}

current_cluster = None

for line in Path("/etc/proxmox-datacenter-manager/remotes.cfg").read_text().splitlines():
    if not line.strip():
        continue


    if line.startswith("pve:"):
        current_cluster = line.split(":", 1)[1].strip()
        inventory["all"]["children"][current_cluster] = {
            "hosts" : {}
        }

    elif line.lstrip().startswith("nodes"):
        node = (
            line.split(None, 1)[1]   # everything after "nodes"
                .split(",", 1)[0]    # remove fingerprint
        )   

        inventory["all"]["children"][current_cluster]["hosts"][node] = {}

with inventory_path.open("w", encoding="utf-8") as f:
    json.dump(inventory, f, indent=2)

print(f"Wrote inventory to {inventory_path}")