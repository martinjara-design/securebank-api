# Almacenamiento corregido para el laboratorio.
# La clave KMS se declarará en compute.tf.

resource "aws_dynamodb_table" "transactions" {
  name         = "securebank-lab-transactions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "transaction_id"

  attribute {
    name = "transaction_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.data.arn
  }

  deletion_protection_enabled = true

  tags = {
    Name = "securebank-lab-transactions"
  }
}

resource "aws_ecr_repository" "api" {
  name                 = "securebank-lab-api"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.data.arn
  }

  tags = {
    Name = "securebank-lab-api"
  }
}

resource "aws_ebs_volume" "data" {
  availability_zone = "us-east-1a"
  size              = 20
  type              = "gp3"

  encrypted  = true
  kms_key_id = aws_kms_key.data.arn

  tags = {
    Name = "securebank-lab-data"
  }
}
