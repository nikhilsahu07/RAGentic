output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "Public DNS name of the ALB"
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "backend_ecr_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "frontend_ecr_repository_url" {
  value = aws_ecr_repository.frontend.repository_url
}
