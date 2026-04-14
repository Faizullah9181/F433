terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.68"
    }
  }
}

resource "digitalocean_droplet" "this" {
  name     = var.name
  region   = var.region
  size     = var.size
  image    = var.image
  ssh_keys = var.ssh_key_ids
  tags     = var.tags

  user_data = var.user_data

  monitoring = true
  ipv6       = true
  backups    = var.backups

  lifecycle {
    ignore_changes = [user_data]
  }
}
