import requests
import json

# The URL of our new endpoint
API_URL = "http://127.0.0.1:5000/generate-challenge"

print(f"Calling API at: {API_URL}")

# Make the POST request (no body needed for this one)
response = requests.post(API_URL)

# Print the results
print(f"\nStatus Code: {response.status_code}")
if response.status_code == 200:
    print("\nResponse JSON:")
    # Use json.dumps for pretty printing
    print(json.dumps(response.json(), indent=2))
else:
    print(f"\nError: {response.text}")