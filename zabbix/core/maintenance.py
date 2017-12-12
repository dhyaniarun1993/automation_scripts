'''
	created by Arun Dhyani
'''

import requests
import json
import sys

URL = 'http://localhost/zabbix/api_jsonrpc.php'
HEADERS = {'content-type': 'application/json'}

def createTimePeriodObject(start_time, start_date=None, period=3600, timeperiod_type=0, day=None, dayofweek=None, every=None, month=None):
	'''
		function to create time period object
	'''
	obj = {
		"timeperiod_type": timeperiod_type,
		"start_time": start_time,
		"period": period
	}

	if start_date:
		obj['start_date'] = start_date
	if day:
		obj['day'] = day
	if dayofweek:
		obj['dayofweek'] = dayofweek
	if every:
		obj['every'] = every
	if month:
		obj['month'] = month

	return obj


def appendcreateTimePeriodObjectList(start_time, start_date=None, period=3600, timeperiod_type=0, day=None, dayofweek=None, every=None, month=None, tpObjList=None):
	'''
		function to create list of time period object or append time period object to provided list
	'''
	if tpObjList:
		objList = tpObjList
	else:
		objList = []

	obj = createTimePeriodObject(start_time, start_date=start_date, period=period, timeperiod_type=timeperiod_type, day=day, dayofweek=dayofweek, every=every, month=month)
	objList.append(obj)
	return objList


def createMaintenance(name, timeperiodObjList, authToken, maintenanceType=0, active_since=None, active_till=None, groupids=None, hostids=None, url=URL, headers=HEADERS):
	'''
		function to create maintenance
	'''

	if groupids or hostids:
		payload = {
			"jsonrpc": "2.0",
			"method": "maintenance.create",
			"params": {
				"name": name,
				"maintenance_type": maintenanceType,
				"timeperiods": timeperiodObjList
			},
			"auth": authToken,
			"id": 1
		}

		if active_since:
			payload['params']['active_since'] = active_since
		if active_till:
			payload['params']['active_till'] = active_till
		if groupids:
			payload['params']['groupids'] = groupids
		if hostids:
			payload['params']['hostids'] = hostids

		print payload

		result = requests.post(url, data=json.dumps(payload), headers=headers).json()
		print result
		if result.has_key('error'):
			return False, result['error']['message']
		else:
			return True, result['result']

	else:
		message = 'Please provide groupids or hostids for maintenance'
		return False, message


def updateMaintenanceUsingId(maintenanceId, authToken, timeperiodObjList=None, hostids=None, groupids=None, active_since=None, active_till=None, url=URL, headers=HEADERS):
	'''
		function to update maintenance
	'''

	payload = {
		"jsonrpc": "2.0",
		"method": "maintenance.update",
		"params": {
			"maintenanceid": maintenanceId,
		},
		"auth": authToken,
		"id": 1
	}

	if groupids:
		payload['params']['groupids'] = groupids
	if hostids:
		payload['params']['hostids'] = hostids
	if timeperiodObjList:
		payload['params']['timeperiods'] = timeperiodObjList
	if active_since:
		payload['params']['active_since'] = active_since
	if active_till:
		payload['params']['active_till'] = active_till	

	print payload

	result = requests.post(url, data=json.dumps(payload), headers=headers).json()
	if result.has_key('error'):
		print result
		return False, result['error']['message']
	else:
		return True, result['result']


def getMaintenanceUsingName(name, authToken, url=URL, headers=HEADERS):

	payload = {
		"jsonrpc": "2.0",
    	"method": "maintenance.get",
    	"params": {
        	"filter": {
        		"name": [
        			name
        		]
        	}
    	},
    	"auth": authToken,
    	"id": 1
	}

	result = requests.post(url, data=json.dumps(payload), headers=headers).json()
	if result.has_key('error'):
		return False, result['error']['message']
	else:
		return True, result['result']


def deleteMaintenanceUsingId(maintenanceId, authToken, url=URL, headers=HEADERS):

	payload = {
		"jsonrpc": "2.0",
    	"method": "maintenance.delete",
    	"params": [
    	    maintenanceId
    	],
    "auth": authToken,
    "id": 1
	}

	result = requests.post(url, data=json.dumps(payload), headers=HEADERS).json()
	if result.has_key('error'):
		return False, result['error']['message']
	else:
		return True, result['result']
