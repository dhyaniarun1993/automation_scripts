'''
	Script to list, register and derigister server from ELB
	developed by Arun Dhyani
'''

import boto3
import argparse
import sys
import json

def get_aws_client(type, region):
	'''
		get aws client based on type
	'''
	return boto3.client(type, region_name=region)


def is_valid_ip(ip_address):
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


def get_instances_behind_elb(elbName, client):
	'''
		function to get instances behind ELB
		requires ELB name and aws elb client
		return instance id list
	'''
	response = client.describe_load_balancers(LoadBalancerNames=[elbName])
	instance_list = []
	try:
		for instance in response['LoadBalancerDescriptions'][0]['Instances']:
			instance_list.append(instance['InstanceId'])
	except Exception, e:
		print('Something went wrong:')
		print str(e)
		sys.exit(1)

	return instance_list


def get_instance_list(instance_list, query_type, client, response_type):
	'''
		function to get instance list(IP and ID) using instance id list or instance ip list based on type
		requires instance list, type and aws ec2 client
		return instance list containing instance id and instance ip
	'''
	result = []
	if query_type == 'id':
		reservations = client.describe_instances(InstanceIds=instance_list)
	elif query_type == 'ip':
		reservations = client.describe_instances(Filters=[{'Name': 'private-ip-address', 'Values': instance_list}])
	for reservation in reservations['Reservations']:
		for instance in reservation['Instances']:
			if response_type == 'id':
				result.append({'InstanceId': instance['InstanceId']})
			elif response_type == 'ip':
				result.append({'PrivateIpAddress': instance['PrivateIpAddress']})
			elif response_type == 'both':
				result.append({
					'InstanceId': instance['InstanceId'],
					'PrivateIpAddress': instance['PrivateIpAddress']
				})
			else:
				print "Invalid response type"
				sys.exit(1)
	return result


def register_deregister_instances(elbName, instance_id_list, action, client):
	'''
		function to register and deregister instance based on type parameter
		requires ELB Name, instance id list, type and aws elb client
	'''
	response = {}
	if action == 'register':
		response = client.register_instances_with_load_balancer(LoadBalancerName=elbName,Instances=instance_id_list)
	elif action == 'deregister':
		response = client.deregister_instances_from_load_balancer(LoadBalancerName=elbName,Instances=instance_id_list)
	else:
		print "Invalid action"
		sys.exit(1)
	return response


def parse_arguments():
    '''
        parse command line arguments
    '''
    parser = argparse.ArgumentParser(description='Script list, register and deregister server from ELB')
    parser.add_argument('-E', '--elb-name', type=str, dest='elb_name', required=True, help='Provide Aws ELB Name')
    parser.add_argument('-R', '--region', type=str, dest='region', required=True, help='Provide Aws region')
    parser.add_argument('-A', '--action', default='list', choices=['list', 'register', 'deregister'], help='list servers, register, or deregister (default: %(default)s)')
    parser.add_argument('-I', '--instance-ip-list', dest='instance_ip_list', nargs='+', help='provide instance ip list to be registered/deregistered from elb')
    args = parser.parse_args()

    if (args.action == 'register' or args.action == 'deregister') and not args.instance_ip_list:
    	parser.error('Please provide Instance IP')
    return args


def main(args):
	elb_client = get_aws_client('elb', args.region)
	ec2_client = get_aws_client('ec2', args.region)
	if args.action == 'list':
		instance_id_list = get_instances_behind_elb(args.elb_name, elb_client)
		instance_list = get_instance_list(instance_id_list, 'id', ec2_client, 'both')
		print json.dumps(instance_list, indent=4, sort_keys=True)
	elif args.action == 'register' or args.action == 'deregister':
		if validate_ip_list(args.instance_ip_list):
			instance_id_list = get_instance_list(args.instance_ip_list, 'ip', ec2_client, 'id')
			response = register_deregister_instances(args.elb_name, instance_id_list, args.action, elb_client)
			print json.dumps(response, indent=4, sort_keys=True)
		else:
			print "IP list is not valid. Please check the IP list."
			print args.instance_ip_list
			sys.exit(1)
	else:
		print "Invalid Action"
		sys.exit(1)

if __name__=='__main__':
    args = parse_arguments()
    main(args)
