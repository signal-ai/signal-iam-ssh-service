#!/usr/bin/env python
#
# Copyright 2018 Signal Media Ltd
# A script that is executed by the sshd authorized_keys command to retrieve active
# public ssh keys from IAM for a specific user for ssh login to AWS instances.

import boto3
import sys, logging
import logging.handlers
import pickle


SYSLOG_ADDRESS = '/dev/log' #for LINUX: /dev/log for OSX /var/run/syslog
CACHE_FILE = '/tmp/iam-cache.p'

# Set up logging to /var/log/secure
logger = logging.getLogger('iam-ssh')
logger.setLevel(logging.INFO)
handler = logging.handlers.SysLogHandler(address=SYSLOG_ADDRESS, facility='authpriv')
formatter = logging.Formatter('%(name)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)



def get_public_key(item):
  '''Function to add key to an array of known allowed keys from AWS'''
  try:
    response = client.get_ssh_public_key(
      UserName=item['UserName'],
      SSHPublicKeyId=item['SSHPublicKeyId'],
      Encoding='SSH'
    )
    return {
    'UserName': response['SSHPublicKey']['UserName'],
    'SSHPublicKey': response['SSHPublicKey']['SSHPublicKeyBody'],
    'SSHPublicKeyId': response['SSHPublicKey']['SSHPublicKeyId'],
    'Status': response['SSHPublicKey']['Status']
  }
  except:
    logger.info('Could not find key for user: {}'.format(item['UserName']))
    return None


def fill_cache():
  users = client.list_users()
  cache = []
  for user in users['Users']:
    list_ssh_keys = client.list_ssh_public_keys(UserName=user['UserName'])
    for item in list_ssh_keys['SSHPublicKeys']:
      key = get_public_key(item)
      if key:
        cache.append(key)
  pickle.dump(cache, open(CACHE_FILE,'wb'))
  return cache

def search_for_active_key(key, cache):
  keys_to_check = list(filter(lambda k: key_to_check in k['SSHPublicKey'], cache))
  allowed_keys = map(lambda k: get_public_key(k), keys_to_check)
  result = list(filter(lambda k: k != None and key_to_check in k['SSHPublicKey'], allowed_keys))
  if result:
    for item in result:
      if 'Active' in item['Status']:
        logger.info('Public key found in IAM for user: {}'.format(item['UserName']))
        print(item['SSHPublicKey'])
      else:
        logger.info('Public key found in IAM for user but user not active: {}'.format(item['UserName']))
    return True
  else:
    return False


if len(sys.argv) > 1:
  key_to_check = sys.argv[1]
  client = boto3.client('iam')
  try:
    cache = pickle.load(open(CACHE_FILE, 'rb'))
  except:
    cache = fill_cache()
  if not search_for_active_key(key_to_check, cache):
    cache = fill_cache()
    if not search_for_active_key(key_to_check, cache):
      logger.info('No user in IAM with active public key matching {}'.format(sys.argv[1]))
else:
  logger.info('No argument passed to iam-ssh.py')
