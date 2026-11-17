resource "aws_cloudwatch_log_group" "vpc_flow" {
  name              = "/securebank/vpc-flow"
  retention_in_days = 365
  kms_key_id        = aws_kms_key.data.arn

  tags = {
    Name = "securebank-lab-vpc-flow"
  }
}

resource "aws_iam_role" "vpc_flow" {
  name = "securebank-lab-vpc-flow-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:ec2:us-east-1:${data.aws_caller_identity.current.account_id}:vpc-flow-log/*"
          }
        }
      }
    ]
  })

  tags = {
    Name = "securebank-lab-vpc-flow-role"
  }
}

resource "aws_iam_role_policy" "vpc_flow" {
  name = "securebank-lab-vpc-flow-policy"
  role = aws_iam_role.vpc_flow.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "WriteFlowLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams",
        ]
        Resource = [
          aws_cloudwatch_log_group.vpc_flow.arn,
          "${aws_cloudwatch_log_group.vpc_flow.arn}:*",
        ]
      }
    ]
  })
}

resource "aws_flow_log" "main" {
  vpc_id               = aws_vpc.main.id
  traffic_type         = "ALL"
  log_destination_type = "cloud-watch-logs"
  log_destination      = aws_cloudwatch_log_group.vpc_flow.arn
  iam_role_arn         = aws_iam_role.vpc_flow.arn

  max_aggregation_interval = 60

  depends_on = [
    aws_iam_role_policy.vpc_flow,
  ]

  tags = {
    Name = "securebank-lab-vpc-flow"
  }
}
