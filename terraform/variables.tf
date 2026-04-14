# ─── Provider ────────────────────────────────────────────

variable "digitalocean_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

# ─── Mode toggle ─────────────────────────────────────────

variable "create_droplet" {
  description = "true = provision a new droplet; false = use existing droplet_id"
  type        = bool
  default     = false
}

# ─── Existing-droplet mode ───────────────────────────────

variable "droplet_id" {
  description = "Existing DigitalOcean droplet ID (used when create_droplet = false)"
  type        = number
  default     = 0
}

# ─── New-droplet settings ────────────────────────────────

variable "droplet_name" {
  description = "Hostname for the new droplet"
  type        = string
  default     = "skynet"
}

variable "droplet_region" {
  description = "DigitalOcean region slug"
  type        = string
  default     = "blr1"
}

variable "droplet_size" {
  description = "Droplet size slug (e.g. s-2vcpu-2gb)"
  type        = string
  default     = "s-2vcpu-2gb"
}

variable "droplet_image" {
  description = "Droplet OS image slug"
  type        = string
  default     = "ubuntu-24-04-x64"
}

variable "ssh_key_ids" {
  description = "SSH key IDs or fingerprints to add to the new droplet"
  type        = list(string)
  default     = []
}

variable "droplet_backups" {
  description = "Enable automated backups on the droplet"
  type        = bool
  default     = false
}

variable "droplet_tags" {
  description = "Tags for the droplet"
  type        = list(string)
  default     = ["f433", "production"]
}

# ─── Domain / SSL ────────────────────────────────────────

variable "domain" {
  description = "Domain name for nginx + certbot (e.g. api.faiz-ai.dev)"
  type        = string
  default     = "api.faiz-ai.dev"
}

variable "certbot_email" {
  description = "Email for Let's Encrypt certificate registration"
  type        = string
  default     = ""
}

# ─── Application secrets (for cloud-init .env) ──────────

variable "google_api_key" {
  description = "Google API key for Gemini"
  type        = string
  sensitive   = true
  default     = ""
}

variable "api_football_key" {
  description = "API-Football key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "gemini_model" {
  description = "Gemini model name"
  type        = string
  default     = "gemini-2.5-flash"
}

variable "llm_backend" {
  description = "LLM backend: google or unsloth"
  type        = string
  default     = "google"
}

variable "cors_origins" {
  description = "Comma-separated CORS origins"
  type        = string
  default     = "http://localhost:3000,http://localhost:5173,https://faiz-ai.dev,https://www.faiz-ai.dev,https://api.faiz-ai.dev,https://f433.faiz-ai.dev"
}

variable "github_repo" {
  description = "GitHub repo to clone (owner/name)"
  type        = string
  default     = "Faizullah9181/F433"
}

# ─── Firewall ────────────────────────────────────────────

variable "create_firewall" {
  description = "Create a DigitalOcean cloud firewall for the droplet"
  type        = bool
  default     = true
}

variable "ssh_allowed_ips" {
  description = "CIDRs allowed to SSH in. Use [\"0.0.0.0/0\",\"::/0\"] for any."
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}

# ─── Project ─────────────────────────────────────────────

variable "project_name" {
  description = "DigitalOcean project name"
  type        = string
  default     = "F433"
}

variable "project_description" {
  description = "DigitalOcean project description"
  type        = string
  default     = "F433 – AI Football Social Arena"
}

variable "project_purpose" {
  description = "DigitalOcean project purpose"
  type        = string
  default     = "Web Application"
}

variable "project_environment" {
  description = "DigitalOcean project environment"
  type        = string
  default     = "Production"
}

variable "additional_resource_urns" {
  description = "Additional existing DigitalOcean resource URNs to include in the project"
  type        = list(string)
  default     = []
}
