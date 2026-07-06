import json
import os
import boto3
from src.utils import ok, server_error

sqs = boto3.client("sqs")
QUEUE_URL = os.environ.get("SQS_COCINA_URL")

def handler(event, context):
    if not QUEUE_URL:
        return server_error("URL de la cola SQS de Cocina no configurada")

    try:
        res = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=5
        )
        
        tasks = []
        for msg in res.get("Messages", []):
            body = json.loads(msg["Body"])
            body["receiptHandle"] = msg["ReceiptHandle"]
            tasks.append(body)

        return ok({"tasks": tasks})
        
    except Exception as e:
        print(f"Error al leer la cola SQS de Cocina: {str(e)}")
        return server_error("Error interno al obtener las tareas operativas")