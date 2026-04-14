variable "name" {
  description = "Droplet hostname"
  type        = string
}

variable "region" {
  description = "DigitalOcean region slug"
  type        = string
}

variable "size" {
  description = "Droplet size slug"
  type        = string
}

variable "image" {
  description = "Droplet image slug"
  type        = string
}

variable "ssh_key_ids" {
  description = "List of SSH key IDs or fingerprints to add to the droplet"
  type        = list(string)
}

variable "tags" {
  description = "Tags to apply to the droplet"
  type        = list(string)
  default     = []
}

variable "user_data" {
  description = "Cloud-init user data script"
  type        = string
  default     = null
}

variable "backups" {
  description = "Enable automated backups"
  type        = bool
  default     = false
}
