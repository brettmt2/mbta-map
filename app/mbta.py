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

def filter_valid_times(station_data: dict[str, list[dict]]) -> dict[str, list[datetime]]:
    now = datetime.now()
    valid = {}

    for child in station_data:
        child_data = station_data[child]
        valid[child] = []
        for trip in child_data:
            arrival = trip.get('attributes').get('arrival_time')
            departure = trip.get('attributes').get('departure_time')
            if arrival:
                time = datetime.fromisoformat(arrival).replace(tzinfo=None)
                # from mbta best practices guide:
                # "If departure_time is null, do not show this prediction because riders won’t be able to board the vehicle."
                if time > now and departure: # valid time:
                    v_id = trip.get('relationships').get('vehicle').get('data').get('id')
                    valid[child].append({
                        "time": time,
                        "v_id": v_id
                    })
                    
        valid[child].sort(key=lambda x: x['time'])

    for child in valid:
        valid[child] = valid[child][:5]

    return valid

async def get_vehicle_status(client: httpx.AsyncClient, v_id: str):
    url = f'https://api-v3.mbta.com/vehicles/{v_id}'
    result = await client.get(url, headers=headers)
    data = result.json()

    return data['data'].get('attributes').get('current_status')

async def get_line_times(client: httpx.AsyncClient, color: str) -> dict[str, dict[str, list[dict]]]:
    line_data = {}
    filtered = [station for station in stc_stations if color in stc_stations[station].get('route')]

    results = await asyncio.gather(
        *[get_station_stop_times(client, station, color) for station in filtered]
    )

    v_ids = set()

    for s, s_results in zip(filtered, results):
        clean = filter_valid_times(station_data=s_results)

        # get each unique vehicle ID to get route status
        for _, trips in clean.items():
            for trip in trips:
                v_ids.add(trip['v_id'])

        line_data[s] = clean

    statuses = await asyncio.gather(
        *[get_vehicle_status(client, id) for id in v_ids]
    )

    status_map = {}
    for v_id, status in zip(v_ids, statuses):
        status_map[v_id] = status

    for s in line_data:
        for _, trips in line_data[s].items():
            for trip in trips:
                trip['status'] = status_map[trip.get('v_id')]

    return line_data

# old approach, found a better solution. this was too many api calls
async def get_child_headsigns(client: httpx.AsyncClient, trip_id: str):
    url = f'https://api-v3.mbta.com/trips/{trip_id}'
    result = await client.get(url, headers=headers) 

    data = result.json()
    data = data['data']

    return data.get('attributes').get('headsign')

if __name__ == "__main__":
    async def main():
        async with httpx.AsyncClient() as client:
            res = await get_line_times(client, 'Red')
            print(res['place-harsq'])
    asyncio.run(main())