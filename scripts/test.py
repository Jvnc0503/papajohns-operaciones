import os
import requests
import sys

def test_endpoints():
    base_url = os.getenv("OPERATIONS_SERVICE_BASE_URL")
    if not base_url:
        print("Error: OPERATIONS_SERVICE_BASE_URL environment variable is not set.")
        sys.exit(1)

    print(f"Testing endpoints at: {base_url}")
    print("-" * 30)

    endpoints = [
        {"name": "Get Tasks Cocina", "method": "GET", "path": "/tasks/cocina"},
        {"name": "Get Tasks Empaque", "method": "GET", "path": "/tasks/empaque"},
        {"name": "Get Tasks Despacho", "method": "GET", "path": "/tasks/despacho"},
    ]

    for endpoint in endpoints:
        url = f"{base_url.rstrip('/')}{endpoint['path']}"
        try:
            response = requests.request(endpoint['method'], url)
            print(f"[{endpoint['name']}] {endpoint['method']} {url} - Status: {response.status_code}")
            print(f"Response Content: {response.text}")
        except Exception as e:
            print(f"[{endpoint['name']}] Failed: {e}")

    # Test updateOrderStatus (requires tenantId and id)
    update_url = f"{base_url.rstrip('/')}/tenants/test-tenant/orders/123/status"
    payload = {"status": "completed"}
    try:
        response = requests.patch(update_url, json=payload)
        print(f"[Update Order Status] PATCH {update_url} - Status: {response.status_code}")
    except Exception as e:
        print(f"[Update Order Status] Failed: {e}")

if __name__ == "__main__":
    test_endpoints()
