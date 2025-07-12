from dataclasses import dataclass, field
from enum import IntEnum
from this import d


# --- Unit Types ---
class UnitType(IntEnum):
    WORKER = 0
    FIGHTER = 1
    SCOUT = 2


UNIT_TYPE_NAMES = {
    UnitType.WORKER: "Раб",
    UnitType.FIGHTER: "Боец",
    UnitType.SCOUT: "Разв",
}


@dataclass(frozen=True, slots=True)
class UnitTypeStats:
    health: int
    attack: int
    capacity: int
    view: int
    speed: int
    prob: float


UNIT_TYPE_STATS = {
    UnitType.WORKER: UnitTypeStats(
        health=130, attack=30, capacity=8, view=1, speed=5, prob=0.6
    ),
    UnitType.FIGHTER: UnitTypeStats(
        health=180, attack=70, capacity=2, view=1, speed=4, prob=0.3
    ),
    UnitType.SCOUT: UnitTypeStats(
        health=80, attack=20, capacity=2, view=4, speed=7, prob=0.1
    ),
}


# --- Food Types ---
class FoodType(IntEnum):
    APPLE = 1
    BREAD = 2
    NECTAR = 3


FOOD_TYPE_NAMES = {
    FoodType.APPLE: "Яблоко",
    FoodType.BREAD: "Хлеб",
    FoodType.NECTAR: "Нектар",
}


@dataclass(frozen=True, slots=True)
class FoodTypeStats:
    calories: int
    spawn: str


FOOD_TYPE_STATS = {
    FoodType.APPLE: FoodTypeStats(calories=10, spawn="случайно на карте"),
    FoodType.BREAD: FoodTypeStats(calories=20, spawn="случайно на карте"),
    FoodType.NECTAR: FoodTypeStats(calories=60, spawn="конвертируется в муравейнике"),
}


# --- Hex Types ---
class HexType(IntEnum):
    ANTHILL = 1
    EMPTY = 2
    DIRT = 3
    ACID = 4
    STONE = 5


HEX_TYPE_NAMES = {
    HexType.ANTHILL: "Муравейник",
    HexType.EMPTY: "Пустой",
    HexType.DIRT: "Грязь",
    HexType.ACID: "Кислота",
    HexType.STONE: "Камни",
}

HEX_TYPE_STATS = {
    HexType.ANTHILL: dict(cost=1, props="см. раздел 'муравейник'"),
    HexType.EMPTY: dict(cost=1, props="-"),
    HexType.DIRT: dict(cost=2, props="стоимость ОП увеличена"),
    HexType.ACID: dict(cost=1, props="наносит 20 урона"),
    HexType.STONE: dict(cost=float("inf"), props="непроходимый гекс"),
}


@dataclass(frozen=True, slots=True)
class Hex:
    q: int
    r: int


@dataclass(frozen=True, slots=True)
class AntConfig:
    allyAttackBonus: float
    attack: dict[str, int]
    foodCapacity: dict[str, int]
    health: dict[str, int]
    prob: dict[str, float]
    speed: dict[str, float]
    view: dict[str, int]


@dataclass(frozen=True, slots=True)
class FoodConfig:
    calories: dict[str, int]
    maxPerTile: int
    maxTilesPerPlayer: int
    tileProbability: float


@dataclass(frozen=True, slots=True)
class MapConfig:
    acidDamage: int
    spotAttackBonus: dict[str, float]
    spotAttackRadius: int
    spotDamage: int
    spotRadius: int
    spotView: int
    version: int


@dataclass(frozen=True, slots=True)
class PlayerConfig:
    ant: AntConfig
    logLimit: int
    unitLimit: int


@dataclass(frozen=True, slots=True)
class Food:
    amount: int
    type: int


@dataclass(frozen=True, slots=True)
class Ant:
    food: Food
    health: int
    id: str
    lastAttack: Hex | None
    lastEnemyAnt: str | None
    q: int
    r: int
    type: int
    lastMove: list[Hex] = field(default_factory=list)
    move: list[Hex] = field(default_factory=list)

    def __str__(self):
        return f"Ant(id={self.id[:8]}, q={self.q}, r={self.r}, type={UnitType(self.type).name})"


@dataclass(frozen=True, slots=True)
class FoodOnMap:
    amount: int
    q: int
    r: int
    type: int


@dataclass(frozen=True, slots=True)
class PlayerEnemy:
    attack: int
    food: Food
    health: int
    q: int
    r: int
    type: int


@dataclass(frozen=True, slots=True)
class PlayerRegistration:
    lobbyEndsIn: int
    name: str
    nextTurn: float
    realm: str


@dataclass(frozen=True, slots=True)
class Tile:
    cost: int
    q: int
    r: int
    type: int


@dataclass(frozen=True, slots=True)
class PlayerResponse:
    ants: list[Ant]
    enemies: list[PlayerEnemy]
    food: list[FoodOnMap]
    home: list[Hex]
    map: list[Tile]
    nextTurnIn: float
    score: int
    spot: Hex
    turnNo: int


@dataclass(frozen=True, slots=True)
class PlayerResponseWithErrors:
    ants: list[Ant]
    enemies: list[PlayerEnemy]
    errors: list[str]
    food: list[FoodOnMap]
    home: list[Hex]
    map: list[Tile]
    nextTurnIn: float
    score: int
    spot: Hex
    turnNo: int


@dataclass(frozen=True, slots=True)
class PublicError:
    code: int
    message: str


@dataclass(frozen=True, slots=True)
class AntMoveCommand:
    """
    Command to move an ant along a path.
    The path should NOT include the ant's current position. It should be a list of hexes to move to, in order, up to the unit's speed.
    If the ant does not move, the path should be an empty list.
    """

    ant: str
    path: list[Hex]


@dataclass(frozen=True, slots=True)
class PlayerMoveCommands:
    moves: list[AntMoveCommand]


@dataclass(frozen=True, slots=True)
class LogMessage:
    message: str
    time: str
