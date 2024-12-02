import logging
import os
from typing import Optional, List
from uuid import uuid4

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator

logger = logging.getLogger()


class LocationInput(BaseModel):
    name: str
    description: str
    longitude: float
    latitude: float

    @field_validator("longitude")
    @classmethod
    def check_location(cls, v: float):
        if not (-180 <= v <= 180):
            raise ValueError('Longitude must be inside (-180.0, 180.0)')
        return v

    @field_validator("latitude")
    @classmethod
    def check_location(cls, v: float):
        if not (-85.05112878 <= v <= 85.05112878):
            raise ValueError('Longitude must be inside (-85.05112878, 85.05112878)')
        return v


class Location(LocationInput):
    id: str


def get_env(var_name: str, default: str) -> str:
    return os.getenv(var_name, default)


def get_int_env(var_name: str, default: int) -> int:
    return int(get_env(var_name, str(default)))


async_redis = redis.Redis(
    connection_pool=redis.BlockingConnectionPool(
        host=get_env("REDIS_HOST", "redis"),
        port=get_int_env("REDIS_PORT", 6379),
        db=get_int_env("REDIS_DB", 0),
    ),
)
app = FastAPI()


def decode_redis_data(data: dict) -> dict:
    return {key.decode(): value.decode() if isinstance(value, bytes) else value for key, value in data.items()}


async def persist_location(location: Location) -> None:
    location_key = f"location:{location.id}"
    logger.warning(location)
    await async_redis.hset(
        location_key,
        mapping=location.dict(),
    )
    await async_redis.geoadd("locations", (location.longitude, location.latitude, location.id))


async def fetch_location(location_id: str) -> Optional[Location]:
    location_data = await async_redis.hgetall(f"location:{location_id}")
    if not location_data:
        return None
    location_data = decode_redis_data(location_data)
    return Location(
        id=location_data["id"],
        name=location_data["name"],
        description=location_data["description"],
        longitude=float(location_data["longitude"]),
        latitude=float(location_data["latitude"]),
    )


async def nearby_locations(longitude: float, latitude: float, unit: str, distance: float) -> List[Location]:
    geo_locations = await async_redis.georadius(
        'locations',
        longitude,
        latitude,
        distance,
        unit,
        withdist=True,
        sort='ASC'
    )
    logger.warning(geo_locations)
    locations_near_me = []

    for geo_location in geo_locations:
        location = await fetch_location(geo_location)
        if location:
            locations_near_me.append(location)

    return locations_near_me


@app.get("/ping")
async def health_check():
    return {"message": "pong"}


@app.get("/location/{location_id}")
async def get_location(location_id: str):
    location = await get_location(location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="location not found")
    return {"location": location}


@app.get("/location/nearby/")
async def get_location(
        latitude: float,
        longitude: float,
        distance: float,
        unit: str = 'km'):
    logger.warning(f'{latitude=}, {longitude=}, {distance=}, {unit=}')
    try:
        locations = await nearby_locations(
            longitude,
            latitude,
            unit,
            distance
        )
    except Exception as e:
        raise
        # raise HTTPException(status_code=500, detail=str(e))
    return {'locations': locations}


@app.post("/location")
async def create_location(location: LocationInput):
    location_id = str(uuid4())
    logger.warning(f'LocationInput: {location}')
    location_to_insert = Location(id=location_id, **location.dict())
    logger.warning(f'Location: {location}')
    try:
        await persist_location(location_to_insert)
        return {"location": location_to_insert, "created": True, "message": "Location Created Successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
