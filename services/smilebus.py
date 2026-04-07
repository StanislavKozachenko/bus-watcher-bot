import logging
import aiohttp

logger = logging.getLogger(__name__)

CITIES_URL = "https://smilebus.by/api/v2/route/cities"
SCHEDULE_URL = "https://smilebus.by/api/v2/route/schedule-detail"


class SmileBusAPI:
    def __init__(self):
        # {city_id: {"name": str, "destinations": [city_id, ...]}}
        self._cities: dict = {}

    async def load_cities(self) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(CITIES_URL) as resp:
                data = await resp.json()

        self._cities = {}
        for city in data.get("data", []):
            from_id = int(city["id_city"])
            self._cities[from_id] = {
                "name": city["city_name"],
                "destinations": [int(d["id_city"]) for d in city.get("cities", [])],
            }
        logger.info("Loaded %d cities from SmileBus API", len(self._cities))

    def all_cities(self) -> dict[int, str]:
        """Returns {city_id: city_name} for all cities."""
        return {cid: info["name"] for cid, info in self._cities.items()}

    def destinations(self, from_id: int) -> dict[int, str]:
        """Returns {city_id: city_name} reachable from from_id."""
        dest_ids = self._cities.get(from_id, {}).get("destinations", [])
        return {cid: self._cities[cid]["name"] for cid in dest_ids if cid in self._cities}

    def city_name(self, city_id: int) -> str:
        return self._cities.get(city_id, {}).get("name", f"город {city_id}")

    async def fetch_schedule(self, date: str, city_from_id: int, city_to_id: int) -> list:
        params = {
            "city_from_id": city_from_id,
            "city_to_id": city_to_id,
            "date": date,
            "stop_from_id": "",
            "stop_to_id": "",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(SCHEDULE_URL, params=params) as resp:
                data = await resp.json()
        return data.get("schedule", [])
