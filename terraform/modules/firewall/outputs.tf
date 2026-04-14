output "id" {
  description = "Firewall ID"
  value       = digitalocean_firewall.this.id
}

output "name" {
  description = "Firewall name"
  value       = digitalocean_firewall.this.name
}
