'''
	Python script to put server in maintenance during deployment
	created by Arun Dhyani
'''

import os
import sys
import time
import datetime
import argparse
from core import auth, host, maintenance

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
TEMP_PATH = os.path.join(ROOT_PATH, 'tmp')

def is_valid_ip(ip_address):
	'''
		function to validate ip 
	'''
	parts = ip_address.split(".")
	if len(parts) != 4:
		return False
	for item in parts:
		if item:
			if not 0 <= int(item) <= 255:
				return False
		else:
			return False
	return True


def validate_ip_list(ip_list):
	'''
		function to validate ip list
	'''
	for ip in ip_list:
		if not is_valid_ip(ip):
			return False
	return True


def parse_arguments():
    '''
        parse command line arguments
    '''
    parser = argparse.ArgumentParser(description='Script to backup_log')
    parser.add_argument('-H', '--url', type=str, dest='url', default='http://localhost/zabbix/api_jsonrpc.php', help='zabbix url')
    parser.add_argument('-u', '--username', dest='username', default='admin', help='zabbix username for authorization')
    parser.add_argument('-p', '--password', dest='password', default='zabbix', help='zabbix password for authorization')
    parser.add_argument('-I', '--server-ip-list', dest='server_ip_list', nargs='+', help='provide instance ip list')
    parser.add_argument('-B', '--build-number', dest='build_number', type=str, required=True, help='provide jenkins build number')
    parser.add_argument('-P', '--prefix', dest='prefix', type=str, required=True, help='provide prefix for maintenance Name')
    parser.add_argument('-A', '--action', default='create', choices=['create', 'delete', 'update'])
    args = parser.parse_args()

    if args.action != "delete":
    	if (args.server_ip_list) and validate_ip_list(args.server_ip_list):
    		return args
        else:
    		parser.error('Invalid IP list')
    else:
    	return args


def main(args):
	maintenanceName = args.prefix + args.build_number

	#login and get auth token
	status, authToken = auth.getAuthToken(user=args.username, password=args.password, url=args.url)
	if not status:
		print("Unable to login into zabbix: %s", authToken)
		sys.exit(1)
	
	#Get maintenanceId from zabbix based on maintenanceName 
	status, maintenanceList = maintenance.getMaintenanceUsingName(maintenanceName, authToken, args.url)
	
	#Unable to get maintenance information from zabbix
	if (not status):
		print("Unable to get maintenance Id against Build Number")
		sys.exit(1)

	elif args.action == "create" or args.action == "update":

		status, raw_hostid_list = host.getHostUsingIP(args.server_ip_list, authToken, url=args.url)
		if not status:
			print("Unable to get hostId list: %s", raw_hostid_list)
			sys.exit(1)

		#convert raw hostId list to hostId list that can be used in POST data for zabbix API 
		hostid_list = host.getHostIdList(raw_hostid_list)

		active_since = int(time.time())
		active_till = active_since + 3600
		start_time = active_since - int(datetime.date.today().strftime('%s'))
		#create time period object required to create maintenance
		timePeriodObj = maintenance.appendcreateTimePeriodObjectList(start_time)	

		#Unable to find maintenance and action is to create maintenance
		if (not maintenanceList) and (args.action == "create"):
			status, result = maintenance.createMaintenance(maintenanceName, timePeriodObj, authToken, active_since=active_since, active_till=active_till, hostids=hostid_list, url=args.url)
			if not status:
				print("Unable to create maintenance: %s" % result)
				sys.exit(1)
			print("Maintenance created with %s" % str(args.server_ip_list))

		#maintenance found and action is to update the maintenance
		elif (maintenanceList) and (len(maintenanceList) == 1) and (args.action == "update"):
			status, result = maintenance.updateMaintenanceUsingId(maintenanceList[0]['maintenanceid'], authToken, timeperiodObjList=timePeriodObj, active_since=active_since, active_till=active_till, hostids=hostid_list, url=args.url)
			if not status:
				print("Unable to update maintenance: %s" % result)
				sys.exit(1)
			print("Maintenance updated with %s" % str(args.server_ip_list))

		else:
			print("Invalid combination")
			sys.exit(1)

	#maintenance found and action is to delete the maintenance
	elif (maintenanceList) and (len(maintenanceList) == 1) and (args.action == "delete"):
		status, result = maintenance.deleteMaintenanceUsingId(maintenanceList[0]['maintenanceid'], authToken, url=args.url)
		if not status:
			print("Unable to delete maintenance: %s" % result)
			sys.exit(1)
		print("Maintenance Deleted")

	else:
		print("Invalid combination")
		sys.exit(1)


if __name__ == '__main__':
	args = parse_arguments()
	main(args)
