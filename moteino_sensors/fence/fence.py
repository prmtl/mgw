#!/usr/bin/env python
import requests
import json
import time
import logging
import argparse

from moteino_sensors import utils

def api_request(url, method='GET', params=None, data=None, auth=None, headers=None, verify_ssl=False):
  try:
    req = requests.request(method, url, params=params,
            data=data, headers=headers, auth=auth, verify=verify_ssl, timeout=2)
    req.raise_for_status()
  except (requests.HTTPError, requests.ConnectionError, requests.exceptions.Timeout) as e:
    LOG.error('Fail to connect to url %s', e)
    return {}
  try:
    data = json.loads(req.text)
  except (ValueError) as e:
    return {}
  return data

def set_armed(mgw_api, status=0):
  params = {'armed': status}
  result = api_request('{}/action/status'.format(mgw_api),
          method='POST', data=json.dumps(params),
          headers={'content-type': 'application/json'})

def check_action(data, allowed_devices, armed, mgw_api):
  status = {
    'enter': 0,
    'exit': 0,
  }
  for device in data:
    action = data[device]['action']
    if device in allowed_devices:
      try:
        status[action] += 1
      except (KeyError):
        pass

  if (armed == 1) and (status['enter'] > 0):
    LOG.info('Disarm alarm')
    set_armed(mgw_api, 0)
  elif (armed == 0) and (status['exit'] == len(allowed_devices)):
    LOG.info('Arm alarm')
    set_armed(mgw_api, 1)

LOG = logging.getLogger(__name__)


def main():
  parser = argparse.ArgumentParser(description='Fence')
  parser.add_argument('--dir', required=True, help='Root directory, should cotains *.config.json')
  args = parser.parse_args()

  conf = utils.load_config(args.dir + '/global.config.json')

  utils.create_logger(logging.INFO)
  logging.getLogger("requests").setLevel(logging.CRITICAL)
  requests.packages.urllib3.disable_warnings()

  LOG.info('Starting')
  while True:
    mgw_status = api_request('{}/action/status'.format(conf['mgw_api']))
    if mgw_status.get('fence'):
      req = api_request(conf['geo_api'], auth=(conf['geo_user'], conf['geo_pass']))
      if req:
        check_action(req, conf['geo_devices'], mgw_status.get('armed'), conf['mgw_api'])
      else:
        set_armed(conf['mgw_api'], 1)

    time.sleep(conf['loop_time'])


if __name__ == "__main__":
  main()
