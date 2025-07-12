from dataclasses import asdict

from dacite import from_dict
from httpx import Client

from game_types import (
    PlayerMoveCommands,
    PlayerRegistration,
    PlayerResponse,
)


class DatsClient:
    def __init__(self, api_token: str, production: bool = False):
        if production:
            url = "https://games.datsteam.dev"
        else:
            url = "https://games-test.datsteam.dev"

        self.client = Client(
            base_url=url,
            headers={"X-Auth-Token": f"{api_token}"},
        )

    def arena(self) -> PlayerResponse:
        response = self.client.get("/api/arena")
        if response.status_code != 200:
            raise Exception(f"Failed to get arena: {response.json()}")
        return from_dict(PlayerResponse, response.json())

    def logs(self):
        response = self.client.get("/api/logs")
        if response.status_code != 200:
            raise Exception(f"Failed to get logs: {response.json()}")
        return response.json()

    def register(self) -> PlayerRegistration:
        response = self.client.post("/api/register")
        if response.status_code != 200:
            raise Exception(f"Failed to register: {response.json()}")
        return from_dict(PlayerRegistration, response.json())

    def move(self, commands: PlayerMoveCommands) -> PlayerResponse:
        response = self.client.post("/api/move", json=asdict(commands))
        if response.status_code != 200:
            raise Exception(f"Failed to move: {response.json()}")
        return from_dict(PlayerResponse, response.json())
