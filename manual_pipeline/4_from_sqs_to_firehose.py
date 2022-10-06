from modules.cloud import AWS, FIREHOSE, S3, SQS, chunker, logger
from modules.static import *
import json

logger.info('Importando constantes')
logger.info(f'Região: {REGION}')
logger.info(f'Account id: {ACCOUNT_ID}')
aws = AWS(REGION, ACCOUNT_ID)
s3 = S3(REGION, ACCOUNT_ID, BUCKET_NAME)
sqs = SQS(REGION, ACCOUNT_ID, SQS_QUEUES[1])
firehose = FIREHOSE(REGION, ACCOUNT_ID, FIREHOSE_DS)
logger.info(f'Lendo mensagens da fila {SQS_QUEUES[1]} no SQS')
sqs_read_messages = sqs.read_message()
while sqs_read_messages != None:
    for sqs_message in sqs_read_messages:
        json_sqs_to_dict = json.loads(sqs_message)
        key = json_sqs_to_dict['MessageBody']['key']
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
    sqs_read_messages = sqs.read_message()
logger.info('Fim do streaming de registros para o Firehose')