#!/usr/bin/env python3
"""
App Store Server Notifications V2 Webhook Receiver.
Handles Apple App Store Server Notifications (JWS decoded), validates
events (SUBSCRIBED, DID_RENEW, EXPIRED, GRACE_PERIOD_EXPIRED), and responds with HTTP 200.

Deployable to VPS, Cloudflare Worker bridge, AWS Lambda, or Docker.
Copyright 2026 Scion Frontiers & Antigravity - Rareș Cristea.
"""

import sys
import os
import json
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def decode_jws_payload(jws_token: str) -> dict:
    """Decodes the unverified payload from an Apple JWS string for inspection."""
    parts = jws_token.split(".")
    if len(parts) != 3:
        return {"error": "Invalid JWS token format"}
    payload_b64 = parts[1]
    # Add base64 padding if needed
    rem = len(payload_b64) % 4
    if rem > 0:
        payload_b64 += "=" * (4 - rem)
    try:
        decoded_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(decoded_bytes.decode("utf-8"))
    except Exception as e:
        return {"error": f"Failed to decode JWS payload: {str(e)}"}

class AppStoreNotificationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"healthy","service":"app-store-notifications-v2"}\n')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path in ["/api/v1/app-store-notifications", "/api/v1/sandbox/app-store-notifications"]:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            is_sandbox = "sandbox" in self.path
            env_name = "SANDBOX" if is_sandbox else "PRODUCTION"

            try:
                data = json.loads(post_data.decode("utf-8"))
                signed_payload = data.get("signedPayload")

                if signed_payload:
                    payload = decode_jws_payload(signed_payload)
                    notification_type = payload.get("notificationType", "UNKNOWN")
                    sub_type = payload.get("subtype", "")
                    notification_uuid = payload.get("notificationUUID", "")

                    logging.info(f"[{env_name}] Received Notification: {notification_type} ({sub_type}) | UUID: {notification_uuid}")

                    # Handle common Apple V2 subscription events
                    if notification_type == "SUBSCRIBED":
                        logging.info("--> Initial subscription purchased.")
                    elif notification_type == "DID_RENEW":
                        logging.info("--> Subscription auto-renewed successfully.")
                    elif notification_type == "GRACE_PERIOD_EXPIRED":
                        logging.warning("--> Billing Grace Period (16 days) expired without payment recovery.")
                    elif notification_type == "EXPIRED":
                        logging.warning("--> Subscription expired.")
                    elif notification_type == "REFUND":
                        logging.warning("--> Apple issued a refund. Revoking entitlement.")

                # Apple requires an immediate HTTP 200 response
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"received":true}\n')

            except Exception as e:
                logging.error(f"Error processing notification: {e}")
                self.send_response(200)  # Still acknowledge to prevent endless retries
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port: int = 8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, AppStoreNotificationHandler)
    logging.info(f"App Store Notification Server listening on port {port}...")
    logging.info(f"Endpoints:\n  - POST /api/v1/app-store-notifications\n  - POST /api/v1/sandbox/app-store-notifications\n  - GET  /health")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server stopped.")

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(p)
