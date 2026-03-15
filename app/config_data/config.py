from dataclasses import dataclass
from environs import Env


@dataclass
class GigaChatConnector:
    giga_creds: str
    giga_model: str


@dataclass
class DBConnector:
    db_host: str
    db_port: int
    db_user: str
    db_pass: str
    db_name: str


@dataclass
class RedisConnector:
    redis_host: str
    redis_port: str


@dataclass
class Config:
    giga_connector: GigaChatConnector
    db_connector: DBConnector
    redis_connector: RedisConnector


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)

    return Config(
        giga_connector=GigaChatConnector(
            giga_creds=env('GIGA_CREDS'),
            giga_model=env('GIGA_MODEL'),
        ),
        db_connector=DBConnector(
            db_host=env('DB_HOST'),
            db_port=env('DB_PORT'),
            db_user=env('DB_USER'),
            db_pass=env('DB_PASS'),
            db_name=env('DB_NAME'),
        ),
        redis_connector=RedisConnector(
            redis_host=env('REDIS_HOST'),
            redis_port=env('REDIS_PORT'),
        )
    )
