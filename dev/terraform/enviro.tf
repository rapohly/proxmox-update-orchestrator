locals {
  nodes = [
    "pve-node-01",
    "pve-node-02",
    "pve-node-03",
    "pve-node-04"
  ]
}

resource "proxmox_virtual_environment_vm" "ubuntu_vm_small" {
  count = 4
  name      = "test-vm-${count.index + 1}"
  node_name = local.nodes[count.index % length(local.nodes)]

  # should be true if qemu agent is not installed / enabled on the VM
  stop_on_destroy = true

  bios = "ovmf"

  efi_disk {
    datastore_id = "local-lvm"
    file_format = "raw"
    type    = "4m"
  }
  
  operating_system {
    type = "l26"
  }

  cpu {
    cores        = 2
    type         = "host"
  }

  memory {
    dedicated = 4096
  }

  cdrom {
    file_id = "local:iso/ubuntu-26.04-live-server-amd64.iso"
  }

  disk {
    datastore_id = "local-lvm"
    interface = "virtio0"
    iothread  = true
    discard   = "on"
    size      = 20
  }
  
  network_device {
    bridge = "vmbr0"
    model  = "virtio"
  }
}