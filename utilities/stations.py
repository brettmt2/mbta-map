import os
from dotenv import load_dotenv
import httpx
import asyncio

load_dotenv()

'''
Helper function to get static list of station names.
'''
async def get_station_metadata():
    stations = {}
    url = 'https://api-v3.mbta.com/stops'
    routes = ['Red', 'Orange']
    headers = {
        'accept': 'application/vnd.api+json',
        'x-api-key': os.getenv('API_KEY')
    }

    async with httpx.AsyncClient() as client:
        data = await asyncio.gather(
           *[client.get(url,
               headers=headers, 
               params={
                   'filter[route]': route
               }
            ) for route in routes]
        )

    # get each station metadata per route
    for route, response in zip(routes, data):
        r_data = response.json()['data']

        for s in r_data:
            attrs = s.get('attributes')

            # if station already exists, append extra route
            if s.get('id') in stations:
                stations[s.get('id')].get('route').append(route)
            else:
                stations[s.get('id')] = {
                    "name": attrs.get('name'),
                    "route": [route],
                    "coords": [attrs.get('longitude'), attrs.get('latitude')]
                }

    return stations

data = asyncio.run(get_station_metadata())

print(data)