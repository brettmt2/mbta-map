import os
from dotenv import load_dotenv
import httpx
import asyncio

from datetime import datetime
from static.stc_stations import stc_stations
from static.stc_route_patterns import route_patterns

load_dotenv()

headers = {
    'accept': 'application/vnd.api+json',
    'x-api-key': os.getenv('API_KEY')
}

async def get_station_stop_times(client: httpx.AsyncClient, parent_station: str, color: str) -> dict[str, list[dict]]:
    child_times = {}

    url = 'https://api-v3.mbta.com/predictions'

    data = await asyncio.gather(
        *[client.get(url, params={
            'filter[stop]': parent_station,
            'filter[route]': color,
            'filter[route_pattern]': rp,
            'sort': 'arrival_time'
        }, headers=headers) 
        for rp in route_patterns[color]]
    )

    for (rp, dest), res in zip(route_patterns[color].items(), data):
        rp_data: list = res.json()['data']
        if len(rp_data) > 0:
            # check if destination data exists for a child route yet
            if dest not in child_times:
                child_times[dest] = rp_data
            else:
                child_times[dest] = child_times[dest] + rp_data

    return child_times

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

async def get_line_times(color: str) -> dict[str, dict[str, list[dict]]]:
    line_data = {}
    filtered = [station for station in stc_stations if color in stc_stations[station].get('route')]

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[get_station_stop_times(client, station, color) for station in filtered]
        )

    for s, s_results in zip(filtered, results):
        line_data[s] = s_results
    
    return line_data

# old approach, found a better solution. this was too many api calls
async def get_child_headsigns(client: httpx.AsyncClient, trip_id: str):
    url = f'https://api-v3.mbta.com/trips/{trip_id}'
    result = await client.get(url, headers=headers) 

    data = result.json()
    data = data['data']

    return data.get('attributes').get('headsign')


data = asyncio.run(get_line_times('Red'))
x = data['place-harsq']
