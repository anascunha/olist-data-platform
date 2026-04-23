variable "location" {
  type        = string
  default     = "East US"
  description = "Região da Azure para deploy"
}

variable "prefix" {
  type        = string
  default     = "olist"
  description = "Prefixo para o nome dos recursos"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Ambiente de deployment (dev, prod)"
}
