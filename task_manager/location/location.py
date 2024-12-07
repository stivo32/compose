import logging
from enum import StrEnum
from typing import Optional

import httpx
from pydantic import BaseModel

from task_manager.utils import get_env

logger = logging.getLogger()


class LocationEndpoints(StrEnum):
    GET_LOCATION = '/location/{location_id}'
    LOCATION = '/location'
    NEARBY_LOCATIONS = '/location/nearby/?longitude={longitude}&latitude={latitude}&distance={distance}&unit={unit}'


class Location(BaseModel):
    name: str
    description: str
    longitude: float
    latitude: float
    id: Optional[str] = None


class LocationsNearMe(BaseModel):
    Locations: list[Location]


class LocationService:
    def __init__(self, base_url: str):
        self.base_url = "http://" + base_url

    async def find_location(self, location_id: str) -> Optional[Location]:
        endpoint = LocationEndpoints.GET_LOCATION.format(location_id)
        url = self.base_url + endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            return Location(**response.json()['location'])

    async def add_location(self, location: Location):
        if location.id and (location := await self.find_location(location.id)):
            return location

        endpoint = LocationEndpoints.LOCATION
        url = self.base_url + endpoint
        async with httpx.AsyncClient() as client:
            params = {
                **location.model_dump()
            }
            response = await client.post(url, json=params)
            response.raise_for_status()
            location = response.json()['location']
            return Location(**location)

    async def find_location_near_me(
            self,
            longitude: float,
            latitude: float,
            unit: str,
            distance: float,
            **kwargs
    ) -> list[Location]:
        endpoint = LocationEndpoints.NEARBY_LOCATIONS.format(
            longitude=longitude, latitude=latitude, unit=unit, distance=distance
        )
        url = self.base_url + endpoint

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            return LocationsNearMe(**response.json()['locations'])


def get_location_service() -> LocationService:
    location_service_host = get_env("LOCATION_SERVICE", "localhost:8001")
    return LocationService(base_url=location_service_host)
