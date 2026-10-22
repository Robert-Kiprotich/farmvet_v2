import requests
from .credentials import *

def get_mpesa_access_token():
    """Generate an M-Pesa access token"""
    token_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(token_url, auth=(CONSUMER_KEY, CONSUMER_SECRET))
    token_data = response.json()

    return token_data.get("access_token")