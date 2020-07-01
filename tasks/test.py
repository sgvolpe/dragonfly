import requests

url='http://dragonflytravel.eu.pythonanywhere.com/send_test_mail'
#url='http://127.0.0.1:8000/send_test_mail'
response = requests.get(url, headers=[], data=[])
print (response)