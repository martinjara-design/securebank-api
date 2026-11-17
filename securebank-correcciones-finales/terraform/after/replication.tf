# Los destinos se preparan en la cuenta de laboratorio; no se inventan ARN.
# Deben tener versionado, bloqueo publico y cifrado KMS habilitados.
variable "replication_destinations" {
  description = "Destinos existentes para backups y logs, cada uno con bucket_arn y kms_key_arn"
  type = map(object({
    bucket_arn  = string
    kms_key_arn = string
  }))
  validation {
    condition = (
      length(var.replication_destinations) == 2 &&
      alltrue([for name in ["backups", "logs"] : contains(keys(var.replication_destinations), name)]) &&
      alltrue([for target in values(var.replication_destinations) :
        can(regex("^arn:aws:s3:::[a-z0-9.-]+$", target.bucket_arn)) &&
        can(regex("^arn:aws:kms:[a-z0-9-]+:[0-9]{12}:key/.+$", target.kms_key_arn))
      ])
    )
    error_message = "Se requieren exactamente backups y logs con ARN de bucket y clave KMS validos."
  }
}

resource "aws_iam_role" "replication" {
  name = "securebank-lab-s3-replication"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "s3.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        ArnEquals    = { "aws:SourceArn" = [aws_s3_bucket.backups.arn, aws_s3_bucket.logs.arn] }
      }
    }]
  })
}

resource "aws_iam_role_policy" "replication" {
  name = "securebank-lab-s3-replication"
  role = aws_iam_role.replication.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetReplicationConfiguration", "s3:ListBucket"]
        Resource = [aws_s3_bucket.backups.arn, aws_s3_bucket.logs.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObjectVersionForReplication", "s3:GetObjectVersionAcl", "s3:GetObjectVersionTagging"]
        Resource = ["${aws_s3_bucket.backups.arn}/*", "${aws_s3_bucket.logs.arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:ReplicateObject", "s3:ReplicateDelete", "s3:ReplicateTags"]
        Resource = [for target in values(var.replication_destinations) : "${target.bucket_arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:DescribeKey"]
        Resource = aws_kms_key.data.arn
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Encrypt", "kms:GenerateDataKey", "kms:DescribeKey"]
        Resource = [for target in values(var.replication_destinations) : target.kms_key_arn]
      }
    ]
  })
}

resource "aws_s3_bucket_replication_configuration" "backups" {
  bucket     = aws_s3_bucket.backups.id
  role       = aws_iam_role.replication.arn
  depends_on = [aws_s3_bucket_versioning.backups, aws_iam_role_policy.replication]
  rule {
    id       = "replicate-backups"
    priority = 1
    status   = "Enabled"
    filter {}
    delete_marker_replication { status = "Enabled" }
    source_selection_criteria {
      sse_kms_encrypted_objects { status = "Enabled" }
    }
    destination {
      bucket = var.replication_destinations["backups"].bucket_arn
      encryption_configuration {
        replica_kms_key_id = var.replication_destinations["backups"].kms_key_arn
      }
    }
  }
}

resource "aws_s3_bucket_replication_configuration" "logs" {
  bucket     = aws_s3_bucket.logs.id
  role       = aws_iam_role.replication.arn
  depends_on = [aws_s3_bucket_versioning.logs, aws_iam_role_policy.replication]
  rule {
    id       = "replicate-logs"
    priority = 1
    status   = "Enabled"
    filter {}
    delete_marker_replication { status = "Enabled" }
    destination {
      bucket = var.replication_destinations["logs"].bucket_arn
      encryption_configuration {
        replica_kms_key_id = var.replication_destinations["logs"].kms_key_arn
      }
    }
  }
}
