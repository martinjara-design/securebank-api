# Configuración corregida del laboratorio.
# Preparada para análisis estático; no desplegar todavía.

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
  map_public_ip_on_launch = false

  tags = {
    Name = "securebank-lab-subnet-a"
  }
}

resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.10.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = false

  tags = {
    Name = "securebank-lab-subnet-b"
  }
}

resource "aws_security_group" "api" {
  name        = "securebank-lab-api"
  description = "Acceso interno a la API"
  vpc_id      = aws_vpc.main.id

  # API disponible solamente desde la red interna.
  ingress {
    description = "API desde la VPC"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["10.10.0.0/16"]
  }

  # Salida a PostgreSQL limitada a la subred de datos.
  egress {
    description = "PostgreSQL en subred de datos"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.10.2.0/24"]
  }

  tags = {
    Name = "securebank-lab-api"
  }
}

resource "aws_security_group" "db" {
  name        = "securebank-lab-db"
  description = "PostgreSQL accesible desde el grupo de la API"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL desde la API"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id]
  }

  egress = []

  tags = {
    Name = "securebank-lab-db"
  }
}

resource "aws_default_security_group" "restricted" {
  vpc_id = aws_vpc.main.id

  ingress = []
  egress  = []

  tags = {
    Name = "securebank-lab-default-deny"
  }
}
