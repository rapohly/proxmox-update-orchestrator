#!/usr/bin/env python3

import json
import sys
from dataclasses import dataclass
from typing import List, Optional

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

CPU_WEIGHT = 0.30
RAM_WEIGHT = 0.70

MAX_CPU_UTIL = 0.90
MAX_RAM_UTIL = 0.90

def bytes_to_gib(value):
    return value / (1024 ** 3)

# ---------------------------------------------------------------------
# DATA MODELS
# ---------------------------------------------------------------------

@dataclass
class VM:
    vmid: int
    name: str
    source_node: str
    cpu: float   # CPU units
    ram: float   # GB

@dataclass
class Node:
    name: str

    cpu_capacity: float
    ram_capacity: float

    cpu_used: float
    ram_used: float

    def score(
        self,
        cpu_used: Optional[float] = None,
        ram_used: Optional[float] = None,
    ) -> float:
        """
        Calculate weighted utilization score.
        """

        cpu_used = self.cpu_used if cpu_used is None else cpu_used
        ram_used = self.ram_used if ram_used is None else ram_used

        cpu_util = cpu_used / self.cpu_capacity
        ram_util = ram_used / self.ram_capacity

        return (
            CPU_WEIGHT * cpu_util
            + RAM_WEIGHT * ram_util
        )

    def can_fit(self, vm: VM) -> bool:
        """
        Check thresholds after placement.
        """

        cpu_util = (self.cpu_used + vm.cpu) / self.cpu_capacity
        ram_util = (self.ram_used + vm.ram) / self.ram_capacity

        return (
            cpu_util <= MAX_CPU_UTIL
            and ram_util <= MAX_RAM_UTIL
        )

    def projected_score(self, vm: VM) -> float:
        """
        Score after placing VM on this node.
        """

        return self.score(
            cpu_used=self.cpu_used + vm.cpu,
            ram_used=self.ram_used + vm.ram,
        )

    def place_vm(self, vm: VM):
        self.cpu_used += vm.cpu
        self.ram_used += vm.ram


# ---------------------------------------------------------------------
# VM SORTING
# ---------------------------------------------------------------------

def vm_weight(vm: VM) -> float:
    """
    Weight used for largest-first ordering.

    Normalized so CPU, RAM contribute proportionally.
    """

    return (
        CPU_WEIGHT * vm.cpu
        + RAM_WEIGHT * vm.ram
    )


# ---------------------------------------------------------------------
# GREEDY PLACEMENT
# ---------------------------------------------------------------------

def place_vms(vms: List[VM], nodes: List[Node]):
    placements = []

    # Largest-first
    sorted_vms = sorted(vms, key=vm_weight, reverse=True)

    for vm in sorted_vms:

        candidates = [
            node for node in nodes
            if node.can_fit(vm)
        ]

        if not candidates:
            raise RuntimeError(
                f"No valid destination found for VM {vm.id} ({vm.name})"
            )

        best_node = min(
            candidates,
            key=lambda n: n.projected_score(vm)
        )

        best_node.place_vm(vm)

        placements.append({
            "vmid": vm.vmid,
            "name": vm.name,
            "source_node": vm.source_node,
            "destination_node": best_node.name
        })

    return placements

if __name__ == "__main__":

    inventory_path = "/home/rpohly/projects/proxmox-update-orchestrator/output/proxmox_inventory.json"

    with open(inventory_path, "r") as f:
        data = json.load(f)

    update_node = data["update_node"]

    nodes = [
        Node(
            name=n["node"],
            cpu_capacity=n["maxcpu"],
            ram_capacity=bytes_to_gib(n["mem_total_bytes"]),
            # io_capacity=n["io_capacity"],
            cpu_used=n["cpu"] * n["maxcpu"],
            ram_used=bytes_to_gib(n["mem_used_bytes"]),
            # io_used=n["io_used"],
        )
        for n in data["nodes"]
        if n["node"] != update_node
    ]

    vms = [
        VM(
            vmid=v["vmid"],
            name=v["name"],
            source_node=v.get("node", update_node),
            cpu=v["cpu"] * v["maxcpu"],
            ram=bytes_to_gib(v["mem_used_bytes"]),
        )
        for v in data["vms_to_evac"]
        if v["status"] == "running"
    ]

    try:
        placements = place_vms(vms, nodes)

        output = {
            "update_node": update_node,
            "migration_plan": placements
        }

        output_path = "/home/rpohly/projects/proxmox-update-orchestrator/output/migration_plan.json"

        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

        print(json.dumps(output, indent=2))

    except RuntimeError as e:
        error_output = {
            "error": str(e),
            "update_node": update_node,
            "migration_plan": []
        }

        print(json.dumps(error_output, indent=2))
        sys.exit(1)