# Proxmox Cluster Maintenance Orchestrator

A Python + Ansible-based orchestration tool for performing safe, automated, rolling maintenance across Proxmox clusters. It handles VM evacuation, node updates, reboots, and post-maintenance validation with cluster-aware decision making.

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

* Cluster-aware VM evacuation planning
* Rolling node maintenance (one node at a time)
* Safe migration sequencing for minimal disruption
* Ansible-driven execution layer for reliability and consistency
* Automated wait/retry logic for reboots and service recovery
* Post-maintenance validation checks
* Extensible architecture for custom policies and workflows

---

## Architecture

### Python Orchestrator (Brains)

Responsible for:

* Querying cluster state
* Determining node maintenance order
* Calculating VM migration strategy
* Tracking progress and failure states
* Handling retries and rollback logic

### Ansible Execution Layer (Hands)

Responsible for:

* Draining nodes (migration triggers)
* Running system updates
* Rebooting hosts
* Verifying services and node readiness

---

## Requirements

* Python 3.10+
* Ansible Core (installed via pip)
* Sudo privileges on target nodes
* Linux control machine (recommended)

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

* Create a Python virtual environment
* Install Python dependencies
* Install Ansible and required collections
* Prepare runtime structure

---

## Configuration

Configuration is typically managed via:

* `config.yml` (cluster definition and behavior)
* Ansible inventory file
* Environment variables (optional secrets/credentials)

Example cluster configuration:

```yaml
cluster_name: prod-cluster

nodes:
  - pve01
  - pve02
  - pve03

maintenance:
  rolling: true
  max_parallel_nodes: 1
  verify_services: true
```

---

## Usage

Activate environment:

```bash
source .venv/bin/activate
```

Run maintenance:

```bash
python src/main.py --cluster prod-cluster --mode update
```

Dry-run mode:

```bash
python src/main.py --cluster prod-cluster --mode plan
```

---

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
* VM evacuation is validated before maintenance begins
* Post-reboot health checks are mandatory
* Failures halt the rolling process by default
* No cluster-wide operations occur without explicit orchestration approval

---

## Roadmap

Planned improvements:

* Intelligent VM placement optimization (load-aware balancing)
* Web UI for maintenance monitoring
* Slack/Teams notifications
* Parallel maintenance mode with risk thresholds
* Proxmox API integration enhancements
* Historical maintenance reporting

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
