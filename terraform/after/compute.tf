# Configuración corregida de EC2 y RDS.
# Preparada para análisis estático; no desplegar todavía.

data "aws_ssm_parameter" "amazon_linux" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

resource "aws_instance" "web" {
  ami                         = data.aws_ssm_parameter.amazon_linux.value
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.api.id]
  iam_instance_profile        = aws_iam_instance_profile.api.name
  associate_public_ip_address = false
  monitoring                  = true
  ebs_optimized               = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted   = true
    kms_key_id  = aws_kms_key.data.arn
  }

  tags = {
    Name = "securebank-lab-web"
  }
}

resource "aws_instance" "worker" {
  ami                         = data.aws_ssm_parameter.amazon_linux.value
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.private.id
  vpc_security_group_ids      = [aws_security_group.api.id]
  iam_instance_profile        = aws_iam_instance_profile.api.name
  associate_public_ip_address = false
  monitoring                  = true
  ebs_optimized               = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted   = true
    kms_key_id  = aws_kms_key.data.arn
  }

  tags = {
    Name = "securebank-lab-worker"
  }
}

resource "aws_db_subnet_group" "postgres" {
  name = "securebank-lab-postgres"

  subnet_ids = [
    aws_subnet.public.id,
    aws_subnet.private.id,
  ]

  tags = {
    Name = "securebank-lab-postgres-subnets"
  }
}

resource "aws_db_parameter_group" "postgres" {
  name   = "securebank-lab-postgres16"
  family = "postgres16"

  parameter {
    name         = "log_statement"
    value        = "all"
    apply_method = "immediate"
  }

  parameter {
    name         = "rds.force_ssl"
    value        = "1"
    apply_method = "pending-reboot"
  }

  tags = {
    Name = "securebank-lab-postgres16"
  }
}

resource "aws_iam_role" "rds_monitoring" {
  name = "securebank-lab-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:rds:us-east-1:${data.aws_caller_identity.current.account_id}:db:securebank-lab-postgres"
          }
        }
      }
    ]
  })

  tags = {
    Name = "securebank-lab-rds-monitoring"
  }
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role = aws_iam_role.rds_monitoring.name

  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

resource "aws_db_instance" "postgres" {
  identifier     = "securebank-lab-postgres"
  engine         = "postgres"
  engine_version = "16"
  instance_class = "db.t3.micro"

  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true
  kms_key_id        = aws_kms_key.data.arn

  db_name                     = "securebank"
  username                    = "labadmin"
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  parameter_group_name   = aws_db_parameter_group.postgres.name
  vpc_security_group_ids = [aws_security_group.db.id]

  publicly_accessible                 = false
  multi_az                            = true
  backup_retention_period             = 7
  deletion_protection                 = true
  auto_minor_version_upgrade          = true
  copy_tags_to_snapshot               = true
  iam_database_authentication_enabled = true

  skip_final_snapshot       = false
  final_snapshot_identifier = "securebank-lab-postgres-final"

  enabled_cloudwatch_logs_exports = [
    "postgresql",
    "upgrade",
  ]

  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  performance_insights_kms_key_id        = aws_kms_key.data.arn

  depends_on = [
    aws_iam_role_policy_attachment.rds_monitoring,
  ]

  tags = {
    Name = "securebank-lab-postgres"
  }
}
