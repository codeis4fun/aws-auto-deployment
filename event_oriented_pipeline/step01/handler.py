from modules.cloud import SQS, logger
from modules.static import *

sqs = SQS(REGION, ACCOUNT_ID, SQS_QUEUES[0])

def step01(event, context):
    logger.info(event)

    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    bucket_path = event["Records"][0]["s3"]["object"]["key"]
    
    message = [{"bucket":bucket_name,"key":bucket_path}]
    sqs_send_messages = [sqs_message for sqs_message in sqs.send_messages(message)]    
    
    logger.info(message)
    logger.info(sqs_send_messages)