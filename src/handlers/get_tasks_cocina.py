import json
import os
import boto3
from src.utils import ok, server_error

sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")

QUEUE_URL = os.environ.get("SQS_COCINA_URL")
TABLE_NAME = os.environ.get("ORDERS_TABLE")

def handler(event, context):
    if not QUEUE_URL or not TABLE_NAME:
        return server_error("Configuración de infraestructura faltante")

    table = dynamodb.Table(TABLE_NAME)

    try:
        # 1. Obtener los mensajes cortos (Tokens) desde SQS
        res = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=5
        )
        
        tasks = []
        for msg in res.get("Messages", []):
            sqs_body = json.loads(msg["Body"])
            
            order_id = sqs_body.get("orderId")
            tenant_id = sqs_body.get("tenantId")
            
            # 2. Obtener los datos reales del pedido desde DynamoDB
            db_res = table.get_item(Key={"tenantId": tenant_id, "orderId": order_id})
            order_data = db_res.get("Item", {})

            # 3. Enriquecer (Fusionar) datos de orquestación con datos de negocio
            enriched_task = {
                "orderId": order_id,
                "tenantId": tenant_id,
                "stage": sqs_body.get("stage"),
                "taskToken": sqs_body.get("taskToken"),
                "receiptHandle": msg["ReceiptHandle"],
                # --- Datos de Negocio inyectados desde la BD ---
                "customerName": order_data.get("customerName", "Desconocido"),
                "items": order_data.get("items", []),
                "totalAmount": order_data.get("totalAmount", 0),
                "status": order_data.get("status", "DESCONOCIDO")
            }
            
            tasks.append(enriched_task)

        # 4. Retornar el JSON perfecto al Dashboard
        return ok({"tasks": tasks})
        
    except Exception as e:
        print(f"Error al leer la cola SQS o consultar DB en Cocina: {str(e)}")
        return server_error("Error interno al obtener las tareas operativas")