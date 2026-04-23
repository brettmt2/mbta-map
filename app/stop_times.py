import os
from dotenv import load_dotenv
import httpx
import asyncio

from datetime import datetime
from static.stc_stations import stc_stations

load_dotenv()

headers = {
    'accept': 'application/vnd.api+json',
    'x-api-key': os.getenv('API_KEY')
}

async def get_station_stop_times(client: httpx.AsyncClient, parent_station: str, color: str) -> list[dict]:
    url = 'https://api-v3.mbta.com/predictions'
    params = {
        'filter[stop]': parent_station,
        'filter[route]': color,
        'sort': 'arrival_time'
    }

    result = await client.get(url, params=params, headers=headers)
    data = result.json()
    data = data['data']
    return data

def filter_valid_times(line: str, station_data: list):
    now = datetime.now()
    valid = []
    predictions = None
    
    for trip in predictions:
        trip_type = trip.get('relationships').get('route').get('data').get('id')
        arrival = trip.get('attributes').get('arrival_time')

        if trip_type == line and arrival:
            time = datetime.fromisoformat(arrival).replace(tzinfo=None)
            if time > now: # valid time and route
                trip_id = trip.get('relationships').get('trip').get('data').get('id')
                valid.append([trip_id, time])

    return valid[:5]

async def get_line_times(color: str) -> dict:
    line_data = {}
    filtered = [station for station in stc_stations if color in stc_stations[station].get('route')]

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[get_station_stop_times(client, station, color) for station in filtered]
        )
    
    for s, s_results in zip(filtered, results):
        line_data[s] = s_results

asyncio.run(get_line_times('Red'))
