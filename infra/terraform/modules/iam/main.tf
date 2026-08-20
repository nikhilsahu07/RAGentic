# ── Trust Policy for ECS Tasks ───────────────────────────────────────────────
data "aws_iam_policy_document" "ecs_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# ── 1. ECS Task Execution Role (Infrastructure Level) ───────────────────────
resource "aws_iam_role" "ecs_execution" {
  name               = "ragentic-ecs-execution-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.ecs_trust.json

  tags = {
    Name = "ragentic-ecs-execution-role-${var.environment}"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_standard" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Read secrets from SSM Parameter Store (least-privilege)
resource "aws_iam_policy" "ssm_read" {
  name        = "ragentic-ssm-secrets-${var.environment}"
  description = "Allow ECS task execution role to fetch application secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter"
        ]
        Resource = "arn:aws:ssm:*:*:parameter/ragentic/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_ssm" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = aws_iam_policy.ssm_read.arn
}

# ── 2. ECS Task Role (Application Runtime Level) ────────────────────────────
resource "aws_iam_role" "ecs_task" {
  name               = "ragentic-ecs-task-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.ecs_trust.json

  tags = {
    Name = "ragentic-ecs-task-role-${var.environment}"
  }
}

# Scoped S3 Policy: Only PutObject and GetObject on the specific bucket
resource "aws_iam_policy" "s3_scoped" {
  name        = "ragentic-s3-rw-${var.environment}"
  description = "Least-privilege S3 access for RAG document storage"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ListBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = var.s3_bucket_arn
      },
      {
        Sid    = "ReadWriteObjects"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${var.s3_bucket_arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_s3" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.s3_scoped.arn
}
