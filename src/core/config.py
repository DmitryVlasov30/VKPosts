from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    @property
    def database_url(self):
        return f"sqlite+aiosqlite:///{BASE_DIR}/posts.db"

    db_echo: bool = True


settings = Settings()
