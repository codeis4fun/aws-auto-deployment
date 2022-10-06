import boto3, json, uuid, logging, itertools

logger = logging.getLogger('AWS Services')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

ch.setFormatter(formatter)

logger.addHandler(ch)

def chunker(iterable, chunksize):
    """
    Return elements from the iterable in `chunksize`-ed lists. The last returned
    chunk may be smaller (if length of collection is not divisible by `chunksize`).

    >>> print list(chunker(xrange(10), 3))
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    """
    i = iter(iterable)
    while True:
        wrapped_chunk = [list(itertools.islice(i, int(chunksize)))]
        if not wrapped_chunk[0]:
            break
        yield wrapped_chunk.pop()

class AWS():
    logger.info('Instanciando classe AWS')
    def __init__(self, region: str, account_id: str):
        """Inicia as variáveis globais do ambiente da AWS definidos em variables.py.

        Args:
            region (str): região onde a infraestrutura foi deployada via Terraform e Serverless.
            account_id (str): identificador da conta da AWS.
        """
        self.region = region
        self.account_id = account_id
        self.session = boto3.Session()

class S3(AWS):
    logger.info('Instanciando classe S3 e herdando atributos da classe AWS')
    def __init__(self, region: str, account_id: str, bucket_name: str):
        """Inicia as variáveis globais do S3 para utilizar os métodos abaixo.

        Args:
            region (str): região onde a infraestrutura foi deployada via Terraform e Serverless.
            account_id (str): identificador da conta da AWS.
            bucket_name (str): nome do bucket deployado via Terraform.
        """
        self.bucket_name = bucket_name
        super().__init__(region, account_id)
        self.s3_client = self.session.client('s3')
        
    def list_objects(self, prefix: str):
        """Lista os objetos com um determinado prefixo.

        Args:
            prefix (str): Prefixo a ser utilizado para filtrar a listagem de objetos no bucket.

        Returns:
            Uma lista contendo um dicionário com o nome do bucket e a key para o objeto.
        """
        self._prefix = prefix
        try:
            objects = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self._prefix
            )
        except:
            logger.error('Bucket ou prefixo não encontrado')
            return 'Bucket ou prefix não encontrado'
        paths = [{'bucket': self.bucket_name, 'key': content['Key']} for content in objects['Contents']]

        return paths
    
    def read_object(self, key: str, file_type: str):
        """Lê um objeto do S3.

        Args:
            key (str): caminho do objeto dentro do bucket.
            file_type (str): o tipo de arquivo pode ser csv ou json.

        Returns:
            Retorna o conteúdo do CSV ou JSON lido no S3 com encoding UTF-8.
        """
        self._key = key
        self._file_type = "text/csv; charset=UTF-8" if file_type == 'csv' else "application/json; charset=UTF-8"
        response = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=self._key,
            ResponseContentEncoding="UTF-8",
            ResponseContentType=self._file_type
        )
        if 'Body' in response:
            if self._file_type == "text/csv; charset=UTF-8":
                return response['Body'].read()
            else:
                return response['Body'].iter_lines()
        return None

    def write_object(self, key: str, body: str):
        """Escreve um objeto no S3 com o conteúdo e caminho especificado.

        Args:
            key (str): caminho do objeto dentro do bucket.
            body (str): conteúdo do objeto a ser escrito no bucket.

        Returns:
            Retorna verdadeiro se a escrita for bem sucessidade ou retorna
            o conteúdo da Exception.
        """
        self._key = key
        self._body = body
        try:
            response = self.s3_client.put_object(Bucket=self.bucket_name, Key=self._key, Body=self._body)
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                return True
        except Exception as e:
            logger.exception(e)
            return e    

class SQS(AWS):
    logger.info('Instanciando classe SQS e herdando atributos da classe AWS')
    def __init__(self, region: str, account_id: str, queue_name: str):
        """Inicia as variáveis globais do SQS para utilizar os métodos abaixo.

        Args:
            region (str): região onde a infraestrutura foi deployada via Terraform e Serverless.
            account_id (str): identificador da conta da AWS.
            queue_name (str): Nome da fila no SQS.
        """
        self._queue_name = queue_name
        super().__init__(region, account_id)
        self._url = f'https://sqs.{self.region}.amazonaws.com/{self.account_id}/{self._queue_name}'
        self._sqs_client = self.session.client('sqs', region_name=self.region, endpoint_url=self._url)
    
    def send_messages(self, list_objects: list):
        """Envia uma payload JSON para uma fila do SQS.

        Args:
            list_objects (list): Lista de objetos encontrados dentro do S3.

        Returns:
            Retorna um objeto JSON com metadados do envio.
        """
        self._list_objects = list_objects
        messages = [{'Id': str(uuid.uuid1()), 'MessageBody': object} for object in self._list_objects]
        for message in messages:
            dispatch = self._sqs_client.send_message(
                QueueUrl=self._url,
                MessageBody=json.dumps(message),
                DelaySeconds=3
            )
            yield dispatch
        return dispatch

    
    def _delete_message(self, receipt_handle: dict):
        """Deleta uma mensagem de uma fila do SQS após ter sido lida.

        Args:
            receipt_handle (dict):
            O receipt_handle está associado a uma instancia específica recebendo uma mensagem.
            Se você recebe uma mensagem mais de uma vez, o receipt_handle é diferente a cada vez que receber essa mensagem.
            Leia mais: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.delete_message

        Returns:
            Retorna verdadeiro se a mensagem for deletada da fila com sucesso.
            Se houver algum problema, retorna falso.
        """
        self._receipt_handle = receipt_handle
        try:
            self._sqs_client.delete_message(
                QueueUrl=self._url,
                ReceiptHandle=self._receipt_handle)
            return True
        except Exception as e:
            logger.exception(e)
            return False    

    def read_message(self):
        """Lê uma mensagem de uma fila do SQS e imediatamente a deleta da fila.

        Returns:
            Retorna uma lista de dicionários contendo o conteúdo das mensagens.
        """
        queue_messages = self._sqs_client.receive_message(
            QueueUrl=self._url,
            MaxNumberOfMessages=10
        )
        if "Messages" in queue_messages:
            messages = [message['Body'] for message in queue_messages['Messages']]
            receipts_handle = [message['ReceiptHandle'] for message in queue_messages['Messages']]

            for receipt_handle in receipts_handle:
               self._delete_message(receipt_handle)
            return messages
        return None

class FIREHOSE(AWS):
    logger.info('Instanciando classe Firehose e herdando atributos da classe AWS')
    def __init__(self, region: str, account_id: str, delivery_stream_name: str):
        """Inicia as variáveis globais do Firehose para utilizar os métodos abaixo.

        Args:
            region (str): região onde a infraestrutura foi deployada via Terraform e Serverless.
            account_id (str): identificador da conta da AWS.
            delivery_stream_name (str): nome do delivery stream que vai enviar para o S3.
        """
        super().__init__(region, account_id)
        self._delivery_stream_name = delivery_stream_name
        self._firehose_client = self.session.client('firehose', region_name=self.region)
    
    def put_records(self, records: list, mode: str):
        """Envia os registros em dois modos. O batch junta um número `MAX_BATCH_SIZE` de registros e envia ao firehose.
        Se não for em modo batch, cada registro é enviado separadamente.

        Args:
            records (list): um ou mais registros que foram lidos do JSON
            mode (str): modo escolhido para enviar os dados ao Firehose.

        Returns:
            Returna um objeto com os metadados do envio dos registros ao Firehose.
        """
        self._records = records
        if mode == "batch":
            stream_records = self._firehose_client.put_record_batch(
                DeliveryStreamName=self._delivery_stream_name,
                Records=self._records
            )
        else:
            stream_records = self._firehose_client.put_record(
                DeliveryStreamName=self._delivery_stream_name,
                Record=self._records
            )
        
        return stream_records