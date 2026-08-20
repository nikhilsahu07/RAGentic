variable "environment" {
  type        = string
  description = "Environment name"
  default     = "prod"
}

variable "s3_bucket_arn" {
  type        = string
  description = "ARN of the S3 bucket for documents"
}
