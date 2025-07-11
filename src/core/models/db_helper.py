from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import settings


class DataBaseHelper:
    def __init__(self, url: str, echo: bool = False):
        self.engin = create_async_engine(
            url=url,
            echo=echo,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engin,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )


db_helper = DataBaseHelper(settings.database_url, settings.db_echo)
