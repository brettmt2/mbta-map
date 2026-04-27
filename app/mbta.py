import os
from dotenv import load_dotenv
import httpx
import asyncio

from datetime import datetime, timezone
from app.static.stations import stations
from app.static.route_patterns import route_patterns
from app.utils import realtime_display

load_dotenv(override=False)

def get_headers():
    return {
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
        }, headers=get_headers()) 
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

def filter_valid_times(now, station_data: dict[str, list[dict]]) -> dict[str, list[datetime]]:
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
                    stop_id = trip.get('relationships').get('stop').get('data').get('id')
                    valid[child].append({
                        "time": time,
                        "v_id": v_id,
                        "stop_id": stop_id
                    })
                    
        valid[child].sort(key=lambda x: x['time'])

    return valid
    
async def get_vehicle_status(client: httpx.AsyncClient, v_id: str):
    url = f'https://api-v3.mbta.com/vehicles/{v_id}'
    result = await client.get(url, headers=get_headers())
    data = result.json()

    return data['data'].get('attributes').get('current_status'), data['data'].get('relationships').get('stop').get('data').get('id')

async def get_line_times(client: httpx.AsyncClient, color: str) -> dict[str, dict[str, list[dict]]]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    line_data = {}
    filtered = [station for station in stations if color in stations[station].get('route')]

    results = await asyncio.gather(
        *[get_station_stop_times(client, station, color) for station in filtered]
    )

    v_ids = set()

    for s, s_results in zip(filtered, results):
        clean = filter_valid_times(now, station_data=s_results)

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
        status_map[v_id] = {'status': status[0], 'stop_id': status[1]}

    for s in line_data:
        for _, trips in line_data[s].items():
            for trip in trips:
                trip['status'] = status_map[trip.get('v_id')]['status']
                trip['v_curr_stop'] =  status_map[trip.get('v_id')]['stop_id']
        
        line_data[s] = realtime_display(now, line_data[s])

    return line_data

# old approach, found a better solution. this was too many api calls
async def get_child_headsigns(client: httpx.AsyncClient, trip_id: str):
    url = f'https://api-v3.mbta.com/trips/{trip_id}'
    result = await client.get(url, headers=get_headers()) 

    data = result.json()
    data = data['data']

    return data.get('attributes').get('headsign')

if __name__ == "__main__":
    async def main():
        async with httpx.AsyncClient() as client:
            res = await get_line_times(client, 'Red')

            print(res['place-harsq'])
    asyncio.run(main())