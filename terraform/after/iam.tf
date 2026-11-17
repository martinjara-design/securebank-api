# Identidades y permisos del modelo de infraestructura.
# Este archivo no conecta por sí solo GitHub Actions con AWS.

resource "aws_iam_role" "api" {
  name = "securebank-lab-api-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "securebank-lab-api-role"
  }
}

resource "aws_iam_policy" "api" {
  name        = "securebank-lab-api-policy"
  description = "Acceso limitado a los recursos del laboratorio"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TransactionTableAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
        ]
        Resource = aws_dynamodb_table.transactions.arn
      },
      {
        Sid    = "BackupObjectsAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
        ]
        Resource = "${aws_s3_bucket.backups.arn}/*"
      },
      {
        Sid      = "ListBackupBucket"
        Effect   = "Allow"
        Action   = "s3:ListBucket"
        Resource = aws_s3_bucket.backups.arn
      },
      {
        Sid    = "UseDataEncryptionKey"
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey",
          "kms:DescribeKey",
        ]
        Resource = aws_kms_key.data.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api" {
  role       = aws_iam_role.api.name
  policy_arn = aws_iam_policy.api.arn
}

resource "aws_iam_instance_profile" "api" {
  name = "securebank-lab-api-profile"
  role = aws_iam_role.api.name
}

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com",
  ]

  tags = {
    Name = "securebank-lab-github-oidc"
  }
}

resource "aws_iam_role" "ci" {
  name                 = "securebank-lab-ci-role"
  max_session_duration = 3600

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            "token.actions.githubusercontent.com:sub" = "repo:martinjara-design/securebank-api:ref:refs/heads/main"
          }
        }
      }
    ]
  })

  tags = {
    Name = "securebank-lab-ci-role"
  }
}
