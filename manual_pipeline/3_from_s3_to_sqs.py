from modules.cloud import AWS, S3, SQS, logger
from modules.static import *
logger.info('Importando constantes')
logger.info(f'Região: {REGION}')
logger.info(f'Account id: {ACCOUNT_ID}')
aws = AWS(REGION, ACCOUNT_ID)
s3 = S3(REGION, ACCOUNT_ID, BUCKET_NAME)
logger.info(f'Listando objetos do bucket {BUCKET_NAME} em {JSON_BUCKET}')
objects = s3.list_objects(JSON_BUCKET)
sqs = SQS(REGION, ACCOUNT_ID, SQS_QUEUES[1])
logger.info(f'Enviando os objetos encontrados para a fila {SQS_QUEUES[1]} do SQS')
sqs_send_messages = [sqs_message for sqs_message in sqs.send_messages(objects)]
logger.info('Fim do envio dos objetos ao SQS')