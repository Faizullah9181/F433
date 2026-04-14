output "project_id" {
  description = "Project ID"
  value       = digitalocean_project.this.id
}

output "project_name" {
  description = "Project name"
  value       = digitalocean_project.this.name
}

output "project_resources" {
  description = "Attached resource URNs"
  value       = digitalocean_project.this.resources
}
