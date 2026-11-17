# Configuración inicial para análisis estático.
# Contiene problemas intencionales para el ejercicio.
# No ejecutar terraform apply sobre esta versión.

resource "aws_vpc" "main" {
  cidr_block           = "10.10.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "securebank-lab-vpc"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.10.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "securebank-lab-public"
  }
}

resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.10.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = false

  tags = {
    Name = "securebank-lab-private"
  }
}

resource "aws_security_group" "api" {
  name        = "securebank-lab-api"
  description = "Security group inicial de la API"
  vpc_id      = aws_vpc.main.id

  # Problema intencional: SSH abierto a Internet.
  ingress {
    description = "SSH sin restriccion de origen"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Acceso directo a la API desde cualquier origen.
  ingress {
    description = "API expuesta directamente"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Salida sin restricciones"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "securebank-lab-api"
  }
}

resource "aws_security_group" "db" {
  name        = "securebank-lab-db"
  description = "Security group inicial de base de datos"
  vpc_id      = aws_vpc.main.id

  # Problema intencional: PostgreSQL abierto a Internet.
  ingress {
    description = "PostgreSQL sin restriccion de origen"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Salida sin restricciones"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "securebank-lab-db"
  }
}
