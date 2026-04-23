# get each distinct route pattern for each line
# then for each station in that line, instead of calling all predictions,
# just call the predictions with the route pattern filtered, thus allowing
# me to know exactly what times are for what destination.import os
from dotenv import load_dotenv
import httpx
import asyncio
import json
import os

load_dotenv()

'''
Helper function to get static list of station names.
Outputs static/stations.json
'''
async def get_line_route_patterns():
    url = 'https://api-v3.mbta.com/route_patterns'
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

    route_patterns = {}
    # get each station metadata per route
    for route, response in zip(routes, data):
        r_data = response.json()['data']
        route_patterns[route] = []

        for route_pattern in r_data:
            route_pattern_id = route_pattern.get('id')
            route_patterns[route].append(route_pattern_id)

    return route_patterns

data = asyncio.run(get_line_route_patterns())

with open("static/route_patterns.json", "w") as f:
    json.dump(data, f, indent=2)