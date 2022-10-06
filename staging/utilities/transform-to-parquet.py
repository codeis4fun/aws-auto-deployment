import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Script generated for node S3 bucket
S3bucket_node1 = glueContext.create_dynamic_frame.from_catalog(
    database="terraform-ci-deploy",
    table_name="raw_json",
    transformation_ctx="S3bucket_node1",
)

# Script generated for node ApplyMapping
ApplyMapping_node2 = ApplyMapping.apply(
    frame=S3bucket_node1,
    mappings=[
        ("bibnum", "int", "bibnum", "int"),
        ("title", "string", "title", "string"),
        ("author", "string", "author", "string"),
        ("isbn", "string", "isbn", "string"),
        ("publicationyear", "string", "publicationyear", "string"),
        ("publisher", "string", "publisher", "string"),
        ("subjects", "string", "subjects", "string"),
        ("itemtype", "string", "itemtype", "string"),
        ("itemcollection", "string", "itemcollection", "string"),
        ("floatingitem", "string", "floatingitem", "string"),
        ("itemlocation", "string", "itemlocation", "string"),
        ("reportdate", "string", "reportdate", "string"),
        ("itemcount", "int", "itemcount", "int"),
        ("partition_0", "string", "partition_0", "string"),
        ("partition_1", "string", "partition_1", "string"),
        ("partition_2", "string", "partition_2", "string"),
        ("partition_3", "string", "partition_3", "string"),
    ],
    transformation_ctx="ApplyMapping_node2",
)

# Script generated for node S3 bucket
S3bucket_node3 = glueContext.getSink(
    path="s3://terraform-ci-deploy/parquet/",
    connection_type="s3",
    updateBehavior="UPDATE_IN_DATABASE",
    partitionKeys=[],
    compression="gzip",
    enableUpdateCatalog=True,
    transformation_ctx="S3bucket_node3",
)
S3bucket_node3.setCatalogInfo(
    catalogDatabase="terraform-ci-deploy", catalogTableName="parquet"
)
S3bucket_node3.setFormat("glueparquet")
S3bucket_node3.writeFrame(ApplyMapping_node2)
job.commit()
