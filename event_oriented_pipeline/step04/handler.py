from modules.cloud import FIREHOSE, S3, chunker, logger
from modules.static import *
import json

s3 = S3(REGION, ACCOUNT_ID, BUCKET_NAME)
firehose = FIREHOSE(REGION, ACCOUNT_ID, FIREHOSE_DS)

def step04(event, context):
    logger.info(event)
    
    logger.info(f'Lendo mensagens da fila {SQS_QUEUES[1]} no SQS')
    
    for record in event['Records']: 
        key = json.loads(record['body'])['MessageBody']['key']
        logger.info(f'Lendo {key} no S3')
        read_s3_object = s3.read_object(key, 'json')

        ## Envio ao firehose em batch records
        logger.info('Preparando para o envio em batch de mensagens ao Firehose')
        for chunk_record in chunker(read_s3_object, MAX_BATCH_SIZE):
            batch_records = list(map(lambda record: {'Data':record}, chunk_record))
            logger.info(f'Carga com {MAX_BATCH_SIZE} registros enviada')
            firehose.put_records(batch_records, 'batch')
        ## Envio ao firehose em batch records
    logger.info('Lendo novamente a fila do SQS')