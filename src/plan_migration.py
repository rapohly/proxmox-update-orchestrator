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
class Workload:
    vmid: int
    name: str
    workload_type: str  # "vm" or "ct"
    source_node: str
    cpu: float
    ram: float

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

    def can_fit(self, workload: Workload) -> bool:
        cpu_util = (self.cpu_used + workload.cpu) / self.cpu_capacity
        ram_util = (self.ram_used + workload.ram) / self.ram_capacity

        return (
            cpu_util <= MAX_CPU_UTIL
            and ram_util <= MAX_RAM_UTIL
        )

    def projected_score(self, workload: Workload) -> float:
        return self.score(
            cpu_used=self.cpu_used + workload.cpu,
            ram_used=self.ram_used + workload.ram,
    )

    def place_workload(self, workload: Workload):
        self.cpu_used += workload.cpu
        self.ram_used += workload.ram


# ---------------------------------------------------------------------
# VM SORTING
# ---------------------------------------------------------------------

def workload_weight(workload: Workload) -> float:
    return (
        CPU_WEIGHT * workload.cpu
        + RAM_WEIGHT * workload.ram
    )

# ---------------------------------------------------------------------
# GREEDY PLACEMENT
# ---------------------------------------------------------------------

def place_workloads(workloads: List[Workload], nodes: List[Node]):
    placements = []

    sorted_workloads = sorted(workloads, key=workload_weight, reverse=True)

    for workload in sorted_workloads:
        candidates = [
            node for node in nodes
            if node.can_fit(workload)
        ]

        if not candidates:
            raise RuntimeError(
                f"No valid destination found for {workload.workload_type} "
                f"{workload.vmid} ({workload.name})"
            )

        best_node = min(
            candidates,
            key=lambda n: n.projected_score(workload)
        )

        best_node.place_workload(workload)

        placements.append({
            "type": workload.workload_type,
            "vmid": workload.vmid,
            "name": workload.name,
            "source_node": workload.source_node,
            "destination_node": best_node.name
        })

    return placements

if __name__ == "__main__":

    inventory_path = (
        "/home/rpohly/projects/proxmox-update-orchestrator/"
        "runstate/proxmox_inventory.json"
    )

    with open(inventory_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    update_node = data["update_node"]

    nodes = [
        Node(
            name=n["node"],
            cpu_capacity=n["maxcpu"],
            ram_capacity=bytes_to_gib(n["mem_total_bytes"]),
            cpu_used=n["cpu"] * n["maxcpu"],
            ram_used=bytes_to_gib(n["mem_used_bytes"]),
        )
        for n in data["nodes"]
        if n["node"] != update_node
    ]

    workloads = []

    for v in data["vms_to_evac"]:
        if v["status"] == "running":
            workloads.append(
                Workload(
                    vmid=v["vmid"],
                    name=v["name"],
                    workload_type="vm",
                    source_node=v.get("node", update_node),
                    cpu=v["cpu"] * v["maxcpu"],
                    ram=bytes_to_gib(v["mem_used_bytes"]),
                )
            )

    for c in data["cts_to_evac"]:
        if c["status"] == "running":
            workloads.append(
                Workload(
                    vmid=c["vmid"],
                    name=c["name"],
                    workload_type="ct",
                    source_node=c.get("node", update_node),
                    cpu=c["cpu"] * c["maxcpu"],
                    ram=bytes_to_gib(c["mem_used_bytes"]),
                )
            )

    try:
        placements = place_workloads(workloads, nodes)

        output = {
            "update_node": update_node,
            "migration_plan": placements,
        }

        output_path = (
            "/home/rpohly/projects/proxmox-update-orchestrator/"
            "runstate/migration_plan.json"
        )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        print(json.dumps(output, indent=2))

    except RuntimeError as e:
        error_output = {
            "error": str(e),
            "update_node": update_node,
            "migration_plan": [],
        }

        print(json.dumps(error_output, indent=2))
        sys.exit(1)