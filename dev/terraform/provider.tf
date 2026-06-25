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
  api_token = "terraform@pve!terratoken=703e49c8-93b2-43ab-ba46-c5e7a7f661c3"
  insecure = true
}