import sys

import requests
import json


def send(message):
    # Check if a command-line argument is provided
    # Replace these with your Home Assistant details
    home_assistant_url = "http://10.2.80.47:8123"
    webhook_id = "test-UDhNGYNDLGp8ZABGQKdUReR5"

    # The data you want to send
    data = {
        "message": message
    }

    # Form the full URL
    url = f"{home_assistant_url}/api/webhook/{webhook_id}"

    # Send a POST request with JSON data
    response = requests.post(url, json=data)

    print(f"Response Status Code: {response.status_code}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py 'Your custom message'")
        sys.exit(1)

    # The message is the first argument
    message = sys.argv[1]
    send(message)
