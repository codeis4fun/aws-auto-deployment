BUCKET_NAME = 'abdo6-grupo-k-terraform'
REGION = 'us-west-2'
ACCOUNT_ID = '007774094020'
LANDING_BUCKET = "ingest_csv/"
JSON_BUCKET = "raw_json/"
SQS_QUEUES = ["first-queue", "second-queue"]
FIREHOSE_DS = "firehose-ds"
CSV_COLLUMNS = ["BibNum", "Title", "Author",
            "ISBN", "PublicationYear", "Publisher", "Publisher", 
            "Subjects", "ItemType", "ItemCollection", "FloatingItem", 
            "ItemLocation", "ReportDate", "ItemCount"]
MAX_BATCH_SIZE = 50