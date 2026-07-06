import json
import os
import boto3
from src.utils import ok, server_error, bad_request

sqs = boto3.client("sqs")

def handler(event, context):
    stage = (event.get("pathParameters") or {}).get("stage", "").upper()
    
    queues = {
        "COCINA": os.environ.get("SQS_COCINA_URL"),
        "EMPAQUE": os.environ.get("SQS_EMPAQUE_URL"),
        "DESPACHO": os.environ.get("SQS_DESPACHO_URL")
    }
    
    queue_url = queues.get(stage)
    if not queue_url:
        return bad_request(f"Etapa inválida o cola no configurada: {stage}")

    try:
        # Long polling: Espera 5 segundos para recolectar tareas en batch
        res = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=5
        )
        
        tasks = []
        for msg in res.get("Messages", []):
            body = json.loads(msg["Body"])
            
            # Inyectar el receiptHandle para que el Frontend nos lo devuelva luego
            body["receiptHandle"] = msg["ReceiptHandle"]
            tasks.append(body)

        return ok({"tasks": tasks})
        
    except Exception as e:
        print(f"Error al leer la cola SQS de {stage}: {str(e)}")
        return server_error("Error interno al obtener las tareas operativas")