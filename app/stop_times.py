import os
from dotenv import load_dotenv
import httpx
import asyncio
from static.stc_stations import stc_stations

load_dotenv()

headers = {
    'accept': 'application/vnd.api+json',
    'x-api-key': os.getenv('API_KEY')
}

async def get_station_stop_times(client: httpx.AsyncClient, parent_station: str):
    url = 'https://api-v3.mbta.com/predictions'
    params = {
        'filter[stop]': parent_station,
        'sort': 'arrival_time'
    }

    result = await client.get(url, params=params, headers=headers)
    data = result.json()
    data = data['data']
    return data

async def get_line_times(color: str):

    async with httpx.AsyncClient() as client:
        data = await asyncio.gather(
            *[get_station_stop_times(client, station) 
              for station in stc_stations if color in stc_stations[station].get('route')]
            )

asyncio.run(get_line_times('Red'))