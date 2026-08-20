output "alb_endpoint" {
  value       = "http://${module.compute.alb_dns_name}"
  description = "Public Load Balancer endpoint URL"
}

output "ecs_cluster_name" {
  value       = module.compute.ecs_cluster_name
  description = "ECS cluster name"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.documents.bucket
  description = "S3 bucket for document uploads"
}

output "backend_ecr_url" {
  value       = module.compute.backend_ecr_repository_url
  description = "ECR repository for backend container image"
}

output "frontend_ecr_url" {
  value       = module.compute.frontend_ecr_repository_url
  description = "ECR repository for frontend container image"
}
