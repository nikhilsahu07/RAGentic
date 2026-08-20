variable "environment" {
  type        = string
  description = "Environment name"
  default     = "prod"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs for ALB"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for ECS tasks"
}

variable "alb_security_group_id" {
  type        = string
  description = "ALB Security Group ID"
}

variable "ecs_security_group_id" {
  type        = string
  description = "ECS Task Security Group ID"
}

variable "execution_role_arn" {
  type        = string
  description = "ECS execution role ARN"
}

variable "task_role_arn" {
  type        = string
  description = "ECS task runtime role ARN"
}

variable "milvus_host" {
  type        = string
  description = "Managed/External Milvus Host"
  default     = "milvus.prod.internal"
}

variable "s3_bucket_name" {
  type        = string
  description = "S3 bucket name for documents"
  default     = "ragentic-docs-production"
}
