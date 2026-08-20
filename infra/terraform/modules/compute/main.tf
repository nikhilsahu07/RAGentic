# ── ECR Repositories ────────────────────────────────────────────────────────
resource "aws_ecr_repository" "backend" {
  name                 = "ragentic-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Environment = var.environment
  }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "ragentic-frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Environment = var.environment
  }
}

# ── CloudWatch Log Group for Structured JSON Logs ────────────────────────────
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/ecs/ragentic-${var.environment}"
  retention_in_days = 30

  tags = {
    Environment = var.environment
  }
}

# ── ECS Cluster (Fargate) ───────────────────────────────────────────────────
resource "aws_ecs_cluster" "main" {
  name = "ragentic-cluster-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Environment = var.environment
  }
}

# ── Application Load Balancer ───────────────────────────────────────────────
resource "aws_lb" "main" {
  name               = "ragentic-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids

  tags = {
    Environment = var.environment
  }
}

# Target Group: Backend (FastAPI :8000)
resource "aws_lb_target_group" "backend" {
  name        = "ragentic-backend-tg-${var.environment}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }

  tags = {
    Environment = var.environment
  }
}

# Target Group: Frontend (Next.js :3000)
resource "aws_lb_target_group" "frontend" {
  name        = "ragentic-frontend-tg-${var.environment}"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200-399"
  }

  tags = {
    Environment = var.environment
  }
}

# ALB HTTP Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

# Listener Rule: route /api/* to backend target group
resource "aws_lb_listener_rule" "api_routing" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/docs", "/openapi.json", "/health", "/metrics"]
    }
  }
}

# ── ECS Task Definition (Multi-Container: Backend + Frontend) ───────────────
resource "aws_ecs_task_definition" "app" {
  family                   = "ragentic-task-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024" # 1 vCPU
  memory                   = "2048" # 2 GB
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = "${aws_ecr_repository.backend.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "ENV", value = "production" },
        { name = "LOG_LEVEL", value = "INFO" },
        { name = "MILVUS_HOST", value = var.milvus_host },
        { name = "MILVUS_PORT", value = "19530" },
        { name = "MILVUS_COLLECTION", value = "ragentic_chunks" },
        { name = "S3_BUCKET", value = var.s3_bucket_name },
        { name = "AWS_REGION", value = "us-east-1" },
        { name = "EMBEDDING_MODEL", value = "models/gemini-embedding-001" },
        { name = "LLM_MODEL", value = "gemini-2.5-flash" }
      ]
      secrets = [
        {
          name      = "GEMINI_API_KEY"
          valueFrom = "arn:aws:ssm:us-east-1:*:parameter/ragentic/gemini_api_key"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app_logs.name
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "backend"
        }
      }
    },
    {
      name      = "frontend"
      image     = "${aws_ecr_repository.frontend.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "NODE_ENV", value = "production" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app_logs.name
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "frontend"
        }
      }
    }
  ])

  tags = {
    Environment = var.environment
  }
}

# ── ECS Service ─────────────────────────────────────────────────────────────
resource "aws_ecs_service" "main" {
  name            = "ragentic-service-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 3000
  }

  depends_on = [
    aws_lb_listener.http,
    aws_lb_listener_rule.api_routing
  ]

  tags = {
    Environment = var.environment
  }
}
