terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.68"
    }
  }
}

resource "digitalocean_project" "this" {
  name        = var.name
  description = var.description
  purpose     = var.purpose
  environment = var.environment
  resources   = var.resources
}
