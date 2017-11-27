#!/bin/python

'''
    Created by Arun Dhyani
    Script to backup Logs and send to S3
    This script expects that log filename contains date 
    Script extract date from log filename and create directioy structure as follows
        server_name/date/log_type/
'''

import os, time, sys, json, re, datetime, logging, tarfile
from boto3 import client
import argparse, socket
import requests

def send_slack_alert(message):
    '''
        send slack notification in case of an error
    '''
    hostname = get_server_alias()
    text = {"Server": hostname, "Message": message}
    data = {"text": json.dumps(text),
            "username": "logbackup_bot"}
    try:
        payload = json.dumps(data)
        result = requests.post(slack_webhook, data=payload)
        result.raise_for_status()
    except Exception as e:
        logging.error("Unable to send slack message %s" % str(e))

def put_to_s3(bucket, s3_key, file_path):
    '''
        upload file to s3
    '''
    try:
        aws_s3_client=create_aws_s3_client()
        logging.info('uploading %s to %s bucket at %s' %(file_path, bucket, s3_key))
        aws_s3_client.upload_file(file_path, bucket, s3_key)
        logging.info("File uploaded successfully")
        return True
    except Exception as e:
        message = "Unable to send %s file to S3. Reason:%s" %(file_path, str(e))
        send_slack_alert(message)
        logging.error(message)

def get_server_alias():
    '''
        to get server hostname
    '''
    hostname = socket.gethostname()
    return hostname

def create_aws_s3_client():
    '''
        function to create aws s3 client
    '''
    logging.info("creating aws s3 client")
    ACCESS_KEY=os.getenv("AWS_ACCESS_KEY")
    SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
    if ACCESS_KEY is not None and SECRET_ACCESS_KEY is not None:
        aws_s3_client = client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_ACCESS_KEY)
    else:
        aws_s3_client=client('s3')
    return aws_s3_client

def upload_logs_to_s3(bucket, log_path, log_type, file_list, date_regex):
    server_alias = get_server_alias()
    for file in file_list:
        if os.path.isfile(os.path.join(log_path, file)):
            try:
                match = re.search(date_regex, file)
                log_date = match.group()
                s3_key = os.path.join(server_alias, os.path.join(log_date, os.path.join(log_type, file)))
                is_uploaded = put_to_s3(bucket, s3_key, os.path.join(log_path, file))
                if is_uploaded:
                    os.remove(os.path.join(log_path, file))
            except Exception as e:
                message = "Unable to find date in %s file. Reason: %s" %(log_path, str(e))
                send_slack_alert(message)
                logging.error(message)

def get_file_list(log_path, mtime_threshold):
    '''
        returns a list of files that needs to uploaded to S3
    '''
    logging.info("Backup log script started")
    files=os.listdir(log_path)
    file_list = []
    for file in files:
        last_modified_time = datetime.datetime.fromtimestamp(os.stat(os.path.join(log_path,file)).st_ctime)
        if last_modified_time.date() < mtime_threshold.date():
            logging.info("Backing up %s" %(file))
            file_list.append(file)
    return file_list


def parse_arguments():
    '''
        parse command line arguments
    '''
    parser = argparse.ArgumentParser(description='Script to backup_log')
    parser.add_argument('-p', '--log-path', type=str, dest='log_path', required=True, help='log_file_path')
    parser.add_argument('-t', '--log-type', dest='log_type', required=True)
    parser.add_argument('--date-regex', dest='date_regex', default='\d{8}')
    parser.add_argument('-m', '--mtime', help='modification time in days', required=True)
    parser.add_argument('-b', '--bucket', help='AWS bucket used to backup logs', required=True)
    parser.add_argument('--slack-webhook', dest='slack_webhook', required=True)
    args = parser.parse_args()
    return args

def main(args):
    FORMAT = "%(asctime)-15s %(levelname)s %(lineno)d: %(message)s"
    logging.basicConfig(format=FORMAT,filename="/tmp/backup_log.log",level=logging.INFO)
    global slack_webhook
    slack_webhook = args.slack_webhook
    mtime_threshold = datetime.datetime.fromtimestamp(time.time() - (int(args.mtime) * 86400))
    file_list = get_file_list(args.log_path, mtime_threshold)
    upload_logs_to_s3(args.bucket, args.log_path, args.log_type, file_list, args.date_regex)

if __name__=='__main__':
    args = parse_arguments()
    main(args)
