# Proxmox Cluster Maintenance Orchestrator

A Python + Ansible-based orchestration tool for performing safe, automated, rolling maintenance across Proxmox clusters. It handles VM/CT evacuation, node updates, reboots, and post-maintenance validation with cluster-aware decision making.

---

## Overview

This tool separates **decision-making** from **execution**:

* Python acts as the *orchestrator* ("brains")
* Ansible acts as the *execution layer* ("hands")

It is designed for environments where cluster uptime and controlled maintenance workflows are critical.

Instead of manually coordinating node-by-node maintenance, this tool automates the full lifecycle:

1. Evaluate cluster state
2. Select target node(s)
3. Evacuate workloads safely
4. Perform system updates
5. Reboot nodes
6. Validate health
7. Restore balance

---

## Key Features

* Cluster-aware VM and LXC evacuation planning
* Rolling node maintenance (one node at a time)
* Safe migration sequencing for minimal disruption
* Ansible-driven execution layer for reliability and consistency
* Automated wait/retry logic for service recovery
* Post-maintenance validation checks
* Extensible architecture for custom policies and workflows

---

## Architecture

### Python Orchestrator (Brains)

Responsible for:

* Determining node maintenance order
* Calculating VM/CT migration strategy
* Tracking progress and failure states

### Ansible Execution Layer (Hands)

Responsible for:

* Querying node and VM/CT resource usage
* Draining nodes (migration triggers)
* Running system updates
* Rebooting hosts
* Verifying services and node readiness
* Restoring the initial locations of VMs/CTs

---

## Requirements

* Python 3.10+
* Ansible Core
* Sudo privileges on target nodes
* Proxmox Datacenter Manager
* Working DNS OR a properly defined /etc/hosts file

---

## Installation

```bash
git clone https://your-repo-url/proxmox-maintenance.git
cd proxmox-maintenance

./install.sh
```

---

## install.sh

The installer will:

* Install dependencies
* Query remotes.cfg for the list of configured clusters and nodes
* Prepare runtime structure

---

## Configuration
[Add when ready]

## Ansible Integration

This tool uses Ansible playbooks for all system-level operations.

Example execution flow:

```text
Python -> selects node pve01
Python -> calls Ansible playbook
Ansible -> drains node
Ansible -> runs apt update && apt upgrade
Ansible -> reboots node
Ansible -> waits for SSH
Ansible -> verifies node health
Python -> records success and moves to next node
```

---

## Safety Model

The system is designed with failure containment in mind:

* Only one node is serviced at a time by default
* VM/CT evacuation is validated before maintenance begins
* Post-reboot health checks are mandatory
* Failures halt the rolling process by default
* No cluster-wide operations occur without passing a specific flag (rolling mode)

---

## Roadmap

Planned improvements:

* Improving the input for the LFGMP algorithm
* Web UI for maintenance monitoring
* Historical maintenance reporting
* Logging
* Adjustable batch sizes, with a recommended default estimated by analyzing node metadata
* A simple, easy to use custom CLI

---

## Contributing

Contributions are welcome, especially in:

* Cluster scheduling logic improvements
* Ansible playbook hardening
* Edge case handling in VM migration
* Performance optimizations

---

## License

MIT License (recommended for broad adoption and simplicity)

---

## Author Notes

This tool is designed for real-world Proxmox cluster operations where downtime must be minimized and maintenance must be deterministic, repeatable, and auditable.
