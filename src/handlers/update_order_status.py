import json
import os
import boto3
from datetime import datetime, timezone
from src.utils import ok, bad_request, not_found, server_error, VALID_TRANSITIONS

dynamodb = boto3.resource("dynamodb")
sfn_client = boto3.client("stepfunctions")
sqs_client = boto3.client("sqs")
events_client = boto3.client("events")

TABLE_NAME = os.environ["ORDERS_TABLE"]

def handler(event, context):
    # 1. VALIDACIÓN DE ENTRADA
    tenant_id = (event.get("pathParameters") or {}).get("tenantId")
    order_id = (event.get("pathParameters") or {}).get("id")
    
    if not tenant_id or not order_id:
        return bad_request("Faltan parámetros 'tenantId' o 'id' en la ruta")

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return bad_request("El body no es JSON válido")

    new_status     = body.get("status")
    responsable    = body.get("responsable", "Trabajador")
    task_token     = body.get("taskToken")
    receipt_handle = body.get("receiptHandle")

    if not new_status or new_status not in VALID_TRANSITIONS:
        return bad_request("Estado destino inválido o faltante.")

    # 2. VERIFICACIÓN Y ACTUALIZACIÓN EN DYNAMODB (Idempotencia)
    table = dynamodb.Table(TABLE_NAME)
    result = table.get_item(Key={"tenantId": tenant_id, "orderId": order_id})
    order = result.get("Item")

    if not order:
        return not_found(f"No se encontró el pedido {order_id}.")

    current_status = order["status"]
    
    if current_status == new_status:
        return ok({"message": f"El pedido ya se encuentra en '{new_status}'"})

    expected_prev = VALID_TRANSITIONS[new_status]
    is_valid_transition = (
        current_status in expected_prev if isinstance(expected_prev, list) 
        else current_status == expected_prev
    )

    if not is_valid_transition:
        return bad_request(f"Transición inválida de '{current_status}' a '{new_status}'")

    now = datetime.now(timezone.utc).isoformat()
    
    update_expr = (
        "SET #st = :new_status, updatedAt = :now, "
        "stages.#prev.endedAt = :now, stages.#prev.responsable = :resp, "
        "stages.#next.startedAt = :now"
    )
    
    try:
        table.update_item(
            Key={"tenantId": tenant_id, "orderId": order_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={"#st": "status", "#prev": current_status, "#next": new_status},
            ExpressionAttributeValues={":new_status": new_status, ":now": now, ":resp": responsable},
        )
    except Exception as e:
        print(f"Error actualizando DynamoDB: {str(e)}")
        return server_error("Error de persistencia")

    # 3. LIBERACIÓN DEL FLUJO (Step Functions)
    if task_token:
        try:
            sfn_client.send_task_success(
                taskToken=task_token,
                output=json.dumps({"orderId": order_id, "nextStage": new_status})
            )
        except Exception as e:
            print(f"Error al notificar a Step Functions: {str(e)}")

    # 4. ELIMINACIÓN DE LA TAREA EN COLA (SQS)
    if receipt_handle:
        queues = {
            "COCINA": os.environ.get("SQS_COCINA_URL"),
            "EMPAQUE": os.environ.get("SQS_EMPAQUE_URL"),
            "DESPACHO": os.environ.get("SQS_DESPACHO_URL")
        }
        queue_url = queues.get(current_status) 
        
        if queue_url:
            try:
                sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                print(f"Mensaje borrado exitosamente de {current_status}")
            except Exception as e:
                print(f"Error borrando mensaje SQS: {str(e)}")

    # 5. PROPAGACIÓN DE EVENTOS (EventBridge)
    try:
        events_client.put_events(
            Entries=[{
                "Source": "com.papajohns.orders",
                "DetailType": "OrderStatusUpdated",
                "Detail": json.dumps({
                    "orderId": order_id,
                    "tenantId": tenant_id,
                    "newStatus": new_status,
                    "responsable": responsable,
                    "source": "DASHBOARD"
                }),
                "EventBusName": "default"
            }]
        )
    except Exception as e:
        print(f"Error al emitir evento a EventBridge: {str(e)}")

    return ok({
        "message": f"Pedido actualizado a '{new_status}'",
        "orderId": order_id,
        "newStatus": new_status
    })