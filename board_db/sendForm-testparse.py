#!/usr/bin/env python3
import requests
from parse_log import parse_log

if __name__ == '__main__':
  client = requests.session()

  # Get CSRF token
  url = 'http://localhost:5907/elog/boardtest/create/'
  client.get(url)
  csrftoken = client.cookies['csrftoken']

  # Post data
  data = {'csrfmiddlewaretoken':csrftoken,
          'boardtest-board':"odmb7_rev5#1", 'boardtest-date':'2024-03-30+21:23:51', 'boardtest-location':'1', 'testfilter-prom test': '1', 'testfilter-vme basic test': '1', 'testfilter-fpga clock test': '1', 'testfilter-sysmon test': '1', 'testfilter-ccb test': '1', 'testfilter-otmb test': '1', 'testfilter-lvmb test': '1', 'testfilter-dcfeb jtag test': '1', 'testfilter-dcfeb fast signal test': '1', 'submit_test': 'Submit'
         }
  data = {**data, **parse_log("output_odmb7.txt")}
  print(data)
  req = client.post(url, data=data)
  #print(req)
  #print(req.status_code)
  #print(req.reason)
  #print(req.text)
