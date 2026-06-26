terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "0.111.0"
    }
  }
}

provider "proxmox" {
  endpoint  = "https://pve-node-01.dev.local:8006/"
  api_token = ""
  insecure = true
}