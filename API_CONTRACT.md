# API Contract - Papa Johns Empleados API

## Overview
This document describes the API contract for the Papa Johns Empleados service, which manages tasks across different operational stages (Cocina, Empaque, Despacho).

## Endpoints

### 1. Get Tasks Cocina
- **Method**: `GET`
- **Path**: `/tasks/cocina`
- **Description**: Retrieves the list of tasks currently assigned to the kitchen area.
- **Response (200 OK)**:
  ```json
  {
    "tasks": [
      {
        "orderId": "string",
        "tenantId": "string",
        "stage": "COCINA",
        "taskToken": "string",
        "receiptHandle": "string",
        "customerName": "string",
        "items": [
          {
            "productId": "string",
            "price": "string",
            "quantity": "string"
          }
        ],
        "totalAmount": "string",
        "status": "RECEPCION"
      }
    ]
  }
  ```

### 2. Get Tasks Empaque
- **Method**: `GET`
- **Path**: `/tasks/empaque`
- **Description**: Retrieves the list of tasks currently assigned to the packaging area.
- **Response (200 OK)**:
  ```json
  {
    "tasks": []
  }
  ```

### 3. Get Tasks Despacho
- **Method**: `GET`
- **Path**: `/tasks/despacho`
- **Description**: Retrieves the list of tasks currently assigned to the dispatch area.
- **Response (200 OK)**:
  ```json
  {
    "tasks": []
  }
  ```

### 4. Update Order Status
- **Method**: `PATCH`
- **Path**: `/tenants/{tenantId}/orders/{id}/status`
- **Parameters**:
  - `tenantId` (path, required): The unique identifier for the tenant.
  - `id` (path, required): The unique identifier for the order.
- **Response Codes**:
  - `200 OK`: Order status updated successfully.
  - `400 Bad Request`: Invalid request parameters or business logic violation.
  - `500 Internal Server Error`: Server-side error.

## Data Models

### Task Object
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| orderId | string | Unique identifier for the order | 267c290f... |
| tenantId | string | Identifier for the specific tenant | tenant123 |
| stage | string | The operational stage (e.g., COCINA, EMPAQUE) | COCINA |
| taskToken | string | Token associated with the specific task | AQCUAAAA... |
| receiptHandle | string | Handle for the SQS message | AQEBHSrJ3... |
| customerName | string | Name of the customer | John Doe |
| items | array | List of products in the order | [{"productId": "p1", ...}] |
| totalAmount | string | Total price of the order | 26 |
| status | string | Current status of the task | RECEPCION |

### Item Object
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| productId | string | Unique identifier for the product | p1 |
| price | string | Price of the product | 10.5 |
| quantity | string | Quantity ordered | 2 |
