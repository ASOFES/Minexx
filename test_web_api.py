import requests
base_url = 'https://minexx.onrender.com'
print(f'Testing connection to {base_url}')
try:
    response = requests.get(base_url, timeout=10)
    print(f'Success! Status: {response.status_code}')
except Exception as e:
    print(f'Error: {e}')
