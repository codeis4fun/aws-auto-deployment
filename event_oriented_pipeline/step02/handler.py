from modules.cloud import FIREHOSE, S3, logger
from modules.static import *
import pandas as pd
import io, json

s3 = S3(REGION, ACCOUNT_ID, BUCKET_NAME)
firehose = FIREHOSE(REGION, ACCOUNT_ID, FIREHOSE_DS)

def step02(event, context):
    logger.info(event)
    for record in event['Records']: 
        key = json.loads(record['body'])['MessageBody']['key']
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