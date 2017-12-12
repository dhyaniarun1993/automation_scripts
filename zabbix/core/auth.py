'''
	created by Arun Dhyani
'''
import requests
import json
import sys

URL = 'http://localhost/zabbix/api_jsonrpc.php'
HEADERS = {'content-type': 'application/json'}

def getAuthToken(user='admin', password='zabbix', headers=HEADERS, url=URL):
	'''
		function to get auth token from zabbix
	'''

	authPayload = {
		"jsonrpc": "2.0",
		"method": "user.login",
		"params": {
	    "user": "Admin",
	    "password": "zabbix"
		},
		"id": 1,
		"auth": None
	}

	authToken = requests.post(url, data=json.dumps(authPayload), headers=headers).json()

	if authToken.has_key('error'):
		return False, authToken['error']['data']
	else:
		return True, authToken['result']


