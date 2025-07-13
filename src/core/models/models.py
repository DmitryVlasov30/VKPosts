from sqlalchemy.orm import Mapped, mapped_column

from src.core.models.base import Base


class VkTgChannel(Base):
    __tablename__ = "vk_tg_channel"

    id: Mapped[int] = mapped_column(primary_key=True)
    vk_id: Mapped[int]
    vk_screen: Mapped[str]
    tg_channel: Mapped[str]
    posts_id: Mapped[str]
    quantity: Mapped[int]


class AdvPosts(Base):
    __tablename__ = "adv_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    inf_adv: Mapped[str]
    date_post: Mapped[str]
    tg_vk_posting: Mapped[str]


class TgChannel(Base):
    __tablename__ = "tg_channel"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_channel: Mapped[str]


