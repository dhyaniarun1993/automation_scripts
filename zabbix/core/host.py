'''
	created by Arun Dhyani
'''
import requests
import json
import sys

URL = 'http://localhost/zabbix/api_jsonrpc.php'
HEADERS = {'content-type': 'application/json'}


def getHostIdList(rawHostList):
	'''
		function to convert raw hostId list to hostId list
		[{"hostid": "1011"}] -> ["1011"]
	'''
	hostList = []
	for host in rawHostList:
		hostList.append(host['hostid'])

	return hostList


def getHostUsingIP(ipList, authToken, url=URL, headers=HEADERS):

	payload = {
		"jsonrpc": "2.0",
		"method": "host.get",
		"params": {
			"output": [
				"host"
			],
			"filter": {
				"ip": ipList
			}
		},
		"auth": authToken,
		"id": 1
	}

	hostList = requests.post(url, data=json.dumps(payload), headers=headers).json()
	print hostList
	if hostList.has_key('error'):
		return False, hostList['error']['message']
	else:
		return True, hostList['result']
		