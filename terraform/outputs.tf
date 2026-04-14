# ─── Droplet outputs ─────────────────────────────────────

output "droplet_id" {
  description = "Droplet ID (new or existing)"
  value       = var.create_droplet ? module.droplet[0].id : var.droplet_id
}

output "droplet_ipv4" {
  description = "Droplet public IPv4 address"
  value       = var.create_droplet ? module.droplet[0].ipv4_address : null
}

output "droplet_ipv6" {
  description = "Droplet public IPv6 address"
  value       = var.create_droplet ? module.droplet[0].ipv6_address : null
}

# ─── Firewall outputs ────────────────────────────────────

output "firewall_id" {
  description = "Firewall ID"
  value       = var.create_firewall && var.create_droplet ? module.firewall[0].id : null
}

# ─── Project outputs ─────────────────────────────────────

output "project_id" {
  description = "DigitalOcean project ID"
  value       = module.project.project_id
}

output "project_name" {
  description = "DigitalOcean project name"
  value       = module.project.project_name
}

output "project_resources" {
  description = "Resources attached to the project"
  value       = module.project.project_resources
}
