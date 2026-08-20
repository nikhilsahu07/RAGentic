variable "aws_region" {
  type        = string
  description = "AWS deployment region"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Target environment name"
  default     = "prod"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
  default     = "10.0.0.0/16"
}

variable "milvus_host" {
  type        = string
  description = "Hostname for external/managed Milvus cluster"
  default     = "milvus.prod.internal"
}
