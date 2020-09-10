import requests

url = 'https://api.github.com'
response = requests.get(url)
json_response = response.json()
json_headers = response.headers


def print_d(json):
    for key, value in json.items():
        print(f'{key} : {value}')


print_d(json_response)
print_d(json_headers)
