# ─── Cloud-init template ─────────────────────────────────

locals {
  cloud_init = var.create_droplet ? templatefile("${path.module}/templates/cloud-init.yml", {
    hostname         = var.droplet_name
    domain           = var.domain
    certbot_email    = var.certbot_email
    github_repo      = var.github_repo
    google_api_key   = var.google_api_key
    api_football_key = var.api_football_key
    gemini_model     = var.gemini_model
    llm_backend      = var.llm_backend
    cors_origins     = var.cors_origins
  }) : null
}

# ─── Droplet (conditional) ───────────────────────────────

module "droplet" {
  source = "./modules/droplet"
  count  = var.create_droplet ? 1 : 0

  name        = var.droplet_name
  region      = var.droplet_region
  size        = var.droplet_size
  image       = var.droplet_image
  ssh_key_ids = var.ssh_key_ids
  tags        = var.droplet_tags
  backups     = var.droplet_backups
  user_data   = local.cloud_init
}

# ─── Firewall (conditional) ──────────────────────────────

module "firewall" {
  source = "./modules/firewall"
  count  = var.create_firewall && var.create_droplet ? 1 : 0

  name            = "${var.droplet_name}-fw"
  droplet_ids     = [module.droplet[0].id]
  ssh_allowed_ips = var.ssh_allowed_ips
}

# ─── Resolve droplet URN ─────────────────────────────────

locals {
  droplet_urn = var.create_droplet ? module.droplet[0].urn : "do:droplet:${var.droplet_id}"
  resources   = distinct(concat([local.droplet_urn], var.additional_resource_urns))
}

# ─── Project ─────────────────────────────────────────────

module "project" {
  source = "./modules/project"

  name        = var.project_name
  description = var.project_description
  purpose     = var.project_purpose
  environment = var.project_environment
  resources   = local.resources
}
