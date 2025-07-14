from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import settings


class DataBaseHelper:
    def __init__(self, url: str, echo: bool = False):
        self.engin = create_engine(
            url=url,
            echo=echo,
        )
        self.session_factory = sessionmaker(
            bind=self.engin,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )


db_helper = DataBaseHelper(settings.database_url, settings.db_echo)
