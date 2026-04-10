import os
from dotenv import load_dotenv
import httpx
import asyncio

load_dotenv()

'''
Helper function to get static list of station names.
'''
async def get_station_names():
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

    return data

# asyncio.run(get_station_names())
            

            

            



