variable "name" {
  description = "Firewall name"
  type        = string
}

variable "droplet_ids" {
  description = "Droplet IDs to apply the firewall to"
  type        = list(number)
  default     = []
}

variable "tags" {
  description = "Tags to scope the firewall (alternative to droplet_ids)"
  type        = list(string)
  default     = []
}

variable "ssh_allowed_ips" {
  description = "IP addresses allowed to SSH (CIDR). Use [\"0.0.0.0/0\", \"::/0\"] for any."
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}
