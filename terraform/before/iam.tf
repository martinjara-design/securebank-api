# Configuración inicial para análisis estático.
# Incluye permisos excesivos intencionalmente.
# No ejecutar terraform apply sobre esta versión.

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
  description = "Politica inicial con permisos excesivos"

  # Problema intencional: todas las acciones
  # sobre todos los recursos.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ExcessivePermissions"
        Effect   = "Allow"
        Action   = "*"
        Resource = "*"
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

resource "aws_iam_user" "ci" {
  name = "securebank-lab-ci"

  tags = {
    Name = "securebank-lab-ci"
  }
}
