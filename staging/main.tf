provider "aws" {
    region = var.region
}

terraform {
  backend "s3" {
    bucket = "terraform-ci-deploy"
    key    = "infra-state"
    region = "us-west-2"
  }
}
variable "bucket_name" {
    description = "Bucket principal"
    type = string
}

variable "region" {
    description = "Região onde o deploy da infraestrutura será feito"
    type = string
}

variable "account_id" {
    description = "Accound id do perfil disponível no console da AWS"
    type = string
}

variable "sqs_queues" {
    description = "Lista de objetos contendo o nome das queues"
    type = list(string)
}

variable "landing_bucket" {
  description = "Nome do bucket para onde os arquivos serão enviados inicialmente"
  type = string
}

variable "crawlers" {
  description = "Nome dos crawlers do Glue"
  type = list(string)
}

resource "aws_s3_bucket" "b" {
    bucket = var.bucket_name
}

resource "aws_s3_bucket_acl" "b-acl" {
  bucket = aws_s3_bucket.b.id
  acl    = "private"
  depends_on = [
    aws_s3_bucket.b
  ]
}

resource "aws_s3_object" "object" {
    bucket = var.bucket_name
    source = "utilities/transform-to-parquet.py"
    key = "transform-to-parquet.py"
    depends_on = [
      aws_s3_bucket.b,
      aws_s3_bucket_acl.b-acl
    ]
}

resource "aws_s3_object" "athena-query" {
    bucket = var.bucket_name
    key = "athena-query/"
    depends_on = [
      aws_s3_bucket.b,
      aws_s3_bucket_acl.b-acl
    ]
}

resource "aws_sqs_queue" "queue-dl" {
    for_each = toset(var.sqs_queues)
    name = "${each.value}-dl"
    redrive_allow_policy = jsonencode({
        redrivePermission = "byQueue",
        sourceQueueArns   = ["arn:aws:sqs:${var.region}:${var.account_id}:${each.value}"]
    })
    sqs_managed_sse_enabled = true
}

resource "aws_sqs_queue" "queue" {
    for_each = toset(var.sqs_queues)
    name = "${each.value}"
    max_message_size          = 2048
    message_retention_seconds = 86400
    receive_wait_time_seconds = 10
    redrive_policy = jsonencode({
        deadLetterTargetArn = "arn:aws:sqs:${var.region}:${var.account_id}:${each.value}-dl"
        maxReceiveCount     = 50
    })
    sqs_managed_sse_enabled = true
    depends_on = [
      aws_sqs_queue.queue-dl
    ]
}

resource "aws_iam_role" "firehose-role" {
  name = "firehose-role"

  assume_role_policy = <<EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "sts:AssumeRole",
        "Principal": {
          "Service": "firehose.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": ""
      }
    ]
  }
  EOF
}
resource "aws_iam_role_policy" "firehose-role-policy" {
  name        = "firehose-role-policy"
  role   = aws_iam_role.firehose-role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
        {
          Action = [
            "s3:*",
            "s3-object-lambda:*"
          ]
          Effect   = "Allow"
          Resource = "*"
        },
    ]
    })
  }
resource "aws_kinesis_firehose_delivery_stream" "firehose-ds" {
    name        = "firehose-ds"
    destination = "extended_s3"
    

    extended_s3_configuration {
        role_arn = aws_iam_role.firehose-role.arn
        bucket_arn = aws_s3_bucket.b.arn
        prefix = "ingest_json/"
        error_output_prefix = "ingest_json-error/"
    }
  
}

resource "aws_iam_role" "crawler-role" {
  for_each = toset(var.crawlers)
  name = "crawler-role-${each.value}"

  assume_role_policy = <<EOF
  {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "glue.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
  EOF
}

resource "aws_iam_role_policy" "crawler-role-policy" {
  for_each = toset(var.crawlers)
  name        = "crawler-role-policy"
  role   = aws_iam_role.crawler-role[each.key].id

  policy = <<EOF
{
	"Version": "2012-10-17",
	"Statement": [{
			"Effect": "Allow",
			"Action": [
				"glue:*",
				"s3:GetBucketLocation",
				"s3:ListBucket",
				"s3:ListAllMyBuckets",
				"s3:GetBucketAcl",
				"ec2:DescribeVpcEndpoints",
				"ec2:DescribeRouteTables",
				"ec2:CreateNetworkInterface",
				"ec2:DeleteNetworkInterface",
				"ec2:DescribeNetworkInterfaces",
				"ec2:DescribeSecurityGroups",
				"ec2:DescribeSubnets",
				"ec2:DescribeVpcAttribute",
				"iam:ListRolePolicies",
				"iam:GetRole",
				"iam:GetRolePolicy",
				"cloudwatch:PutMetricData"
			],
			"Resource": [
				"*"
			]
		},
		{
			"Effect": "Allow",
			"Action": [
				"s3:CreateBucket"
			],
			"Resource": [
				"arn:aws:s3:::aws-glue-*"
			]
		},
		{
			"Effect": "Allow",
			"Action": [
				"s3:GetObject",
				"s3:PutObject",
				"s3:DeleteObject"
			],
			"Resource": [
				"arn:aws:s3:::aws-glue-*/*",
				"arn:aws:s3:::*/*aws-glue-*/*",
        "arn:aws:s3:::${var.bucket_name}/*"
			]
		},
		{
			"Effect": "Allow",
			"Action": [
				"s3:GetObject"
			],
			"Resource": [
				"arn:aws:s3:::crawler-public*",
				"arn:aws:s3:::aws-glue-*"
			]
		},
		{
			"Effect": "Allow",
			"Action": [
				"logs:CreateLogGroup",
				"logs:CreateLogStream",
				"logs:PutLogEvents"
			],
			"Resource": [
				"arn:aws:logs:*:*:/aws-glue/*"
			]
		},
		{
			"Effect": "Allow",
			"Action": [
				"ec2:CreateTags",
				"ec2:DeleteTags"
			],
			"Condition": {
				"ForAllValues:StringEquals": {
					"aws:TagKeys": [
						"aws-glue-service-resource"
					]
				}
			},
			"Resource": [
				"arn:aws:ec2:*:*:network-interface/*",
				"arn:aws:ec2:*:*:security-group/*",
				"arn:aws:ec2:*:*:instance/*"
			]
		},
		{
			"Effect": "Allow",
			"Action": [
				"s3:GetObject",
				"s3:PutObject"
			],
			"Resource": [
				"arn:aws:s3:::terraform-ci-deploy/${aws_glue_crawler.crawler[each.key].name}*"
			]
		}
	]
} 
EOF
}

resource "aws_glue_catalog_database" "database" {
  name = var.bucket_name
  catalog_id = var.account_id
}

resource "aws_glue_crawler" "crawler" {
  database_name = aws_glue_catalog_database.database.name
  for_each = toset(var.crawlers)
  name          = "${each.value}"
  role          = aws_iam_role.crawler-role[each.key].arn

  s3_target {
    path = "s3://${aws_s3_bucket.b.bucket}/${each.value}/"
  }

}

resource "aws_glue_job" "transform-to-parquet" {
  name     = "transform-to-parquet"
  role_arn = [for value in aws_iam_role.crawler-role: value.arn][0]
  number_of_workers = 9
  worker_type = "G.1X"
  glue_version = "3.0"

  command {
    script_location = "s3://${aws_s3_bucket.b.bucket}/transform-to-parquet.py"
  }
}