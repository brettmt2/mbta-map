import os
from dotenv import load_dotenv
import httpx
import asyncio
import json

load_dotenv()

routes = ['Red', 'Orange', 'Blue', 'Green-B', 'Green-C', 'Green-D', 'Green-E']

'''
Helper function to get static list of station names.
Outputs static/stations.py
'''
async def get_station_metadata():
    stations = {}
    url = 'https://api-v3.mbta.com/stops'
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

'''
Helper function to get static list of route patterns.
Outputs static/route_patterns.py
'''
async def get_line_route_patterns():
    url = 'https://api-v3.mbta.com/route_patterns'
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

    route_patterns = {}
    # get each route pattern for each line
    for route, response in zip(routes, data):
        r_data = response.json()['data']
        route_patterns[route] = {}

        for route_pattern in r_data:
            route_pattern_id = route_pattern.get('id')
            name: str = route_pattern.get('attributes').get('name')
            dest = name.split('-')[1].strip()
            route_patterns[route][route_pattern_id] = dest

    return route_patterns

# format the time display to follow MBTA's guidelines
# https://www.mbta.com/developers/real-time-display-guidelines
# next, implement departure time, headways fields

def realtime_display(now, data):
    for dest in data:
        keep = []
        dest_data = data[dest]

        if len(dest_data) > 0:
            for obj in dest_data:
                if obj and obj['status']:
                    delta = obj['time'] - now
                    if delta.total_seconds() > 0:
                        secs = int(delta.total_seconds())
                        
                        if secs <= 30:
                            time_str = 'ARR'
                        elif secs <= 90 and obj['v_curr_stop'] == obj['stop_id'] and obj['status'] == 'STOPPED_AT':
                            time_str = 'BRD'
                        else:
                            mins = (secs + 30) // 60
                            if mins >= 60:
                                hours = mins // 60
                                remaining_mins = mins % 60
                                time_str = f'{hours} hr {remaining_mins} min'
                            else:
                                time_str = f'{mins} min'
                        obj['time'] = time_str
                        keep.append(obj)
            data[dest] = keep[:5]

    return data

# data = asyncio.run(get_line_route_patterns())

# with open("app/static/route_patterns.json", "w") as f:
#     json.dump(data, f, indent=2)