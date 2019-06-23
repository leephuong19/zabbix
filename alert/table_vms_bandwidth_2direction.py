#!/usr/bin/python
# coding: utf-8
 
import argparse
import json
import logging
import requests
import datetime
import dateutil.parser
import tabulate

IP_CON = '172.16.1.100' #Khai bao IP endpoint node Controller
INTERVAL = 10 #Khai bao khoang thoi gian lay thong so network may ao (ke tu luc chay script)
TRIGGER = 1  #Khai bao nguong bandwidth can lay (Mbps) (> TRIGGER)
ADMIN_ID='702f594aceac404687f213abacd33e52' #Khai bao ID cua admin project
ADMIN_PASS = 'Welcome123' #Khai bao admin password

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
loger = logging.getLogger(__name__)

def get_token():
    token = 'a'
    try:
        json_payload = {
         "auth": {
         "tenantName": "admin",
         "passwordCredentials": {
                  "username": 'admin',
                  "password": ADMIN_PASS
           }
                  }
          }
 
        headers = {'content-type': 'application/json', 'accept': 'application'}
        response = requests.post(url='http://{0}:35357/v2.0/tokens'.format(IP_CON),
                                       data=json.dumps(json_payload),
                                       headers=headers)
        r = response.json()
        token = r['access']['token']['id']
 
    except Exception as e:
          loger.critical(e)

    return token

def get_host(token, ADMIN_ID, instance_id):
    try:
        headers = {'X-Auth-Token':token}
        response = requests.get(url='http://{0}:8774/v2/{1}/servers/{2}'.format(IP_CON, ADMIN_ID, instance_id), headers=headers)
        r = response.json()
    except Exception as e:
        loger.critical(e)
    return r['server']['OS-EXT-SRV-ATTR:host'], r['server']['name']
 
def get_instance(token,direction):
    li = []
    try:
        headers = {'X-Auth-Token':token}
        timestamp_bottom = (datetime.datetime.utcnow() - datetime.timedelta(minutes = INTERVAL)).isoformat()
        if direction == 'inbound':
          response = requests.get(url='http://{0}:8777/v2/meters/network.incoming.bytes.rate?q.field=timestamp&q.op=ge&q.value={1}'.format(IP_CON, timestamp_bottom), headers=headers)
        else:
          response = requests.get(url='http://{0}:8777/v2/meters/network.outgoing.bytes.rate?q.field=timestamp&q.op=ge&q.value={1}'.format(IP_CON, timestamp_bottom), headers=headers)
        r = response.json()
        for i in range(0, len(r)):
            val = float(r[i]['counter_volume'])*8/1000000
            if val >= TRIGGER:
                instance_id = r[i]['resource_metadata']['instance_id'] 
                t = r[i]['recorded_at']
                time = (dateutil.parser.parse(t) + datetime.timedelta(minutes = 420)).replace(microsecond=0).isoformat()
                value = ("{0:.5f}".format(round(val,2)))
                exist_vms = [['a','b']]
                for j in exist_vms:
                    if instance_id == j[1]:
                       host = j[0]  
                       instance_id = j[1]
                       break   
                    else:
                        (host, instance_name) = get_host(token, ADMIN_ID, instance_id)
                        exist_vms.append([host, instance_id])
                ins_info = (host, instance_id, instance_name, value, time)
                li.append(ins_info) 
    except Exception as e:
        loger.critical(e)
    return li


def table(li):
    try:
        x = [] 
        for i in range(0, len(li)):
            instance = li[i]
            x.append([instance[0], instance[1], instance[2],instance[3],instance[4]]) 
        tab = tabulate.tabulate(x, headers=['Host', 'Instance_ID ', 'Instance_Name ', 'Value (Mbps)  ', 'Time '], tablefmt='html')
        return tab
    except Exception as e:
        loger.critical(e)

def main(direction):
    token = get_token()
    instances = get_instance(token,direction)
    return table(instances)

#if __name__ == '__main__':
#    print main()


