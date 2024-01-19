#!/usr/bin/env python3
import requests

if __name__ == '__main__':
  client = requests.session()

  # Get CSRF token
  url = 'http://localhost:8000/elog/log/create/'
  client.get(url)
  csrftoken = client.cookies['csrftoken']

  # Post data
  data = {'csrfmiddlewaretoken':csrftoken,
          'board':"odmb7_rev4#1", 'date':'2024-01-05+21:23:51', 'location':'2', 'text':'Send to CERN'
         }
  req = client.post(url, data=data)
  print(req)
  #print(req.text)
