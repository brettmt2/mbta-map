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

def filter_valid_times(station_data: list) -> list[list]:
    now = datetime.now()
    valid = []
    
    for trip in station_data:
        arrival = trip.get('attributes').get('arrival_time')

        if arrival:
            time = datetime.fromisoformat(arrival).replace(tzinfo=None)
            if time > now: # valid time
                trip_id = trip.get('relationships').get('trip').get('data').get('id')
                valid.append([trip_id, time])

    return valid

async def get_child_headsigns(client: httpx.AsyncClient, trip_id: str):
    url = f'https://api-v3.mbta.com/trips/{trip_id}'
    result = await client.get(url, headers=headers) 

    data = result.json()
    data = data['data']

    return data.get('attributes').get('headsign')

async def get_line_times(color: str) -> dict:
    line_data = {}
    filtered = [station for station in stc_stations if color in stc_stations[station].get('route')]

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[get_station_stop_times(client, station, color) for station in filtered]
        )

        for s, s_results in zip(filtered, results):
            line_data[s] = filter_valid_times(s_results)

        # time[0] = trip id, time[1] = time, assigning time[2] to be headsign
        for s in line_data:
            headsigns = await asyncio.gather(
                *[get_child_headsigns(client, time[0]) for time in line_data[s]]
            )

            for time, headsign in zip(line_data[s], headsigns):
                time.append(headsign)

    return line_data


data = asyncio.run(get_line_times('Red'))

for station in data:
    if station == 'place-harsq':
        print(data[station])


