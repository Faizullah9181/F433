output "id" {
  description = "Droplet ID"
  value       = digitalocean_droplet.this.id
}

output "urn" {
  description = "Droplet URN"
  value       = digitalocean_droplet.this.urn
}

output "ipv4_address" {
  description = "Public IPv4 address"
  value       = digitalocean_droplet.this.ipv4_address
}

output "ipv6_address" {
  description = "Public IPv6 address"
  value       = digitalocean_droplet.this.ipv6_address
}

output "name" {
  description = "Droplet name"
  value       = digitalocean_droplet.this.name
}
