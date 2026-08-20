terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "RAGentic"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

# ── S3 Bucket for RAG Documents (Isolated) ───────────────────────────────────
resource "aws_s3_bucket" "documents" {
  bucket        = "ragentic-docs-${var.environment}-${var.aws_region}"
  force_destroy = false

  tags = {
    Name = "ragentic-docs-${var.environment}"
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ── 1. Networking Module (VPC, Subnets, Gateways, SGs) ──────────────────────
module "networking" {
  source      = "./modules/networking"
  environment = var.environment
  vpc_cidr    = var.vpc_cidr
}

# ── 2. IAM Module (Least-Privilege Roles & Policies) ────────────────────────
module "iam" {
  source        = "./modules/iam"
  environment   = var.environment
  s3_bucket_arn = aws_s3_bucket.documents.arn
}

# ── 3. Compute Module (ECS Fargate, ALB, ECR, CloudWatch) ───────────────────
module "compute" {
  source                = "./modules/compute"
  environment           = var.environment
  vpc_id                = module.networking.vpc_id
  public_subnet_ids     = module.networking.public_subnet_ids
  private_subnet_ids    = module.networking.private_subnet_ids
  alb_security_group_id = module.networking.alb_security_group_id
  ecs_security_group_id = module.networking.ecs_security_group_id
  execution_role_arn    = module.iam.execution_role_arn
  task_role_arn         = module.iam.task_role_arn
  milvus_host           = var.milvus_host
  s3_bucket_name        = aws_s3_bucket.documents.bucket
}
