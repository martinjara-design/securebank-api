# Configuración inicial para análisis estático.
# Contiene controles ausentes o deshabilitados intencionalmente.
# No ejecutar terraform apply sobre esta versión.

resource "aws_s3_bucket" "backups" {
  bucket_prefix = "securebank-lab-backups-"
  force_destroy = false

  # Sin recursos explícitos de bloqueo de acceso público,
  # versionado, logging o configuración de cifrado.

  tags = {
    Name = "securebank-lab-backups"
  }
}

resource "aws_s3_bucket" "logs" {
  bucket_prefix = "securebank-lab-logs-"
  force_destroy = false

  # Sin recursos explícitos de bloqueo de acceso público,
  # versionado o configuración de cifrado.

  tags = {
    Name = "securebank-lab-logs"
  }
}

resource "aws_dynamodb_table" "transactions" {
  name         = "securebank-lab-transactions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "transaction_id"

  attribute {
    name = "transaction_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = false
  }

  deletion_protection_enabled = false

  tags = {
    Name = "securebank-lab-transactions"
  }
}

resource "aws_ecr_repository" "api" {
  name                 = "securebank-lab-api"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "securebank-lab-api"
  }
}

resource "aws_ebs_volume" "data" {
  availability_zone = "us-east-1a"
  size              = 20
  type              = "gp3"
  encrypted         = false

  tags = {
    Name = "securebank-lab-data"
  }
}
