#!/usr/bin/env python3
import requests

if __name__ == '__main__':
  client = requests.session()

  # Get CSRF token
  url = 'http://localhost:8000/elog/board/create'
  client.get(url)
  csrftoken = client.cookies['csrftoken']

  # Post data
  board_id_range = [1,10]
  # Below orders depend on how board_type and board_location was created
  # 1: odmb7_rev4, 2: odmb5_rev1, 3: odmb7_rev5
  board_type = '2' 
  # 1: ucsb, 2: b904, 3: osu, 4: tamu, 5: rice
  board_location = '1'

  for board_id in range(board_id_range[0],board_id_range[1]+1):
    print(f'Creating board board_type:{board_type} with id:{board_id} at location:{board_location}')
    data = {'csrfmiddlewaretoken':csrftoken,
            'board_id': str(board_id), 
            'board_type': board_type,
            'location': board_location,
           }
    req = client.post(url, data=data)
