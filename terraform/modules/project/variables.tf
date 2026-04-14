variable "name" {
  description = "Project name"
  type        = string
}

variable "description" {
  description = "Project description"
  type        = string
}

variable "purpose" {
  description = "Project purpose"
  type        = string
}

variable "environment" {
  description = "Project environment"
  type        = string
}

variable "resources" {
  description = "List of DigitalOcean resource URNs assigned to this project"
  type        = list(string)
  default     = []
}
