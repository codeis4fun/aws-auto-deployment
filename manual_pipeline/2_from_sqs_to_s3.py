from modules.cloud import AWS, S3, SQS, logger
from modules.static import *
import pandas as pd
import io, json

logger.info('Importando constantes')
logger.info(f'Região: {REGION}')
logger.info(f'Account id: {ACCOUNT_ID}')
aws = AWS(REGION, ACCOUNT_ID)
s3 = S3(REGION, ACCOUNT_ID, BUCKET_NAME)
sqs = SQS(REGION, ACCOUNT_ID, SQS_QUEUES[0])
logger.info(f'Lendo mensagens da fila {SQS_QUEUES[0]} no SQS')
sqs_read_messages = sqs.read_message()
while sqs_read_messages != None:
    for sqs_message in sqs_read_messages:
        json_sqs_to_dict = json.loads(sqs_message)
        key = json_sqs_to_dict['MessageBody']['key']
        json_key = key.replace(LANDING_BUCKET, JSON_BUCKET).replace('.csv', '.json')
        logger.info(f'Lendo {key} no S3')
        read_s3_object = s3.read_object(key, 'csv')
        logger.info('Convertendo o formato CSV em JSON')
        json_object = pd.read_csv(
            io.BytesIO(read_s3_object),
            header=0,
            delimiter=",",
            usecols=CSV_COLLUMNS)\
            .to_json(orient='records', lines=True)
        logger.info(f'Escrevendo arquivo de volta no S3 em {json_key}')
        write_object = s3.write_object(json_key, json_object)
        if write_object:
            logger.info(f"Objeto JSON escrito com sucesso!")
        else:
            logger.error(f"O objeto {json_key} não pode ser escrito!")
    logger.info('Lendo novamente a fila do SQS')        
    sqs_read_messages = sqs.read_message()
logger.info('Fim da conversão dos objetos CSV em JSON')