#!/usr/bin/env python3
import requests

if __name__ == '__main__':

  # Delete board within below range
  board_index_range = [9,11]

  client = requests.session()
  for board_index in range(baord_index_range[0],board_index_range[1]+1):
    print(f'Deleting board_index:{board_index}')
    url = f'http://localhost:8000/elog/board/{board_index}/delete/'
    client.get(url)
    csrftoken = client.cookies['csrftoken']
    data = {'csrfmiddlewaretoken':csrftoken}
    req = client.post(url, data=data)
