"""
Test script to debug bKash credentials
"""
import sys
import os
import django

# Setup Django
sys.path.insert(0, r'd:\Django Project\rhms\rhms\rhms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rhms.settings')
django.setup()

from payment.bkash import get_bkash_credentials, get_bkash_token
import requests

print("=" * 60)
print("bKash Credentials Debug")
print("=" * 60)

# Get credentials
creds = get_bkash_credentials()
print(f"\nUsername: '{creds['username']}'")
print(f"Password: '{creds['password']}'")
print(f"App Key: '{creds['app_key']}'")
print(f"App Secret: '{creds['app_secret']}'")
print(f"Base URL: '{creds['base_url']}'")

print("\n" + "=" * 60)
print("Testing Token Request")
print("=" * 60)

# Try to get token with detailed output
url = f"{creds['base_url']}/tokenized/checkout/token/grant"

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'username': creds['username'],
    'password': creds['password']
}

payload = {
    'app_key': creds['app_key'],
    'app_secret': creds['app_secret']
}

print(f"\nRequest URL: {url}")
print(f"Headers: {headers}")
print(f"Payload: {payload}")

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body: {response.json()}")
except Exception as e:
    print(f"\nError: {str(e)}")
