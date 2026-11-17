# Configuración inicial para análisis estático.
# Contiene problemas intencionales para el ejercicio.
# No ejecutar terraform apply sobre esta versión.

data "aws_ssm_parameter" "amazon_linux" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

resource "aws_instance" "web" {
  ami                         = data.aws_ssm_parameter.amazon_linux.value
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.api.id]
  iam_instance_profile        = aws_iam_instance_profile.api.name
  associate_public_ip_address = true
  monitoring                  = false

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "optional"
  }

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted   = false
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
  monitoring                  = false

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "optional"
  }

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted   = false
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

resource "aws_db_instance" "postgres" {
  identifier     = "securebank-lab-postgres"
  engine         = "postgres"
  instance_class = "db.t3.micro"

  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = false

  db_name                     = "securebank"
  username                    = "labadmin"
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.db.id]

  publicly_accessible     = true
  multi_az                = false
  backup_retention_period = 0
  deletion_protection     = false
  skip_final_snapshot     = true

  tags = {
    Name = "securebank-lab-postgres"
  }
}

resource "aws_kms_key" "data" {
  description             = "Clave del laboratorio SecureBank"
  deletion_window_in_days = 7
  enable_key_rotation     = false

  tags = {
    Name = "securebank-lab-data-key"
  }
}
