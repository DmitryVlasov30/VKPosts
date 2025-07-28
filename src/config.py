import json
from pathlib import Path
from pydantic_settings import BaseSettings

with open("data.json") as data:
    inf = json.load(data)


class Settings(BaseSettings):

    access_token_vk: str = inf["access_token_vk"]
    token_tg: str = inf["token"]
    general_admin: int = inf["general_admin"]
    name_main_table: str = inf["name_table"]
    name_adv_table: str = inf["name_table_adv"]
    black_list: list[str] = inf["blacklist"]
    photo_skip: list[str] = inf["photo_skip"]
    moderators: list[int] = inf["moderators"]
    interval: int = inf["interval"]
    path_to_db: Path = Path(inf["path_to_db"])
    path_to_logs: Path = Path(inf["path_to_logs"])
    replace_words: list[str] = inf["replace_word"]
    name_tg_table: str = inf["all_tg"]
    skip_link: int = inf["skip_link"]


settings = Settings()


