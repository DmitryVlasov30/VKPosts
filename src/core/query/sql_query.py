from sqlalchemy import insert, select, and_, delete, update

from src.core.models.db_helper import db_helper
from src.core.models.models import VkTgChannel, AdvPosts, TgChannel
from src.core.models.base import Base


def create_table():
    Base.metadata.create_all(db_helper.engin)


def drop_table():
    Base.metadata.drop_all(db_helper.engin)


class VkTgTable:

    @staticmethod
    def select_tg_vk() -> list:
        with db_helper.engin.connect() as session:
            query = (
                select(VkTgChannel)
            )

            result = session.execute(query)
            return list(map(lambda el: list(el), result.all()))

    @staticmethod
    def insert_tg_vk(vk_id: int,
                     vk_screen: str,
                     tg_channel: str,
                     posts: str = "") -> str:
        with db_helper.engin.connect() as session:
            new_inf = [{
                "vk_id": vk_id,
                "vk_screen": vk_screen,
                "tg_channel": tg_channel,
                "posts_id": posts,
                "quantity": len(posts.split())
            }]
            stmt = insert(VkTgChannel).values(new_inf)
            session.execute(stmt)
            session.commit()
            return "success"

    @staticmethod
    def delete_tg_vk(vk_id: int, tg_channel: str) -> str:
        with db_helper.engin.connect() as session:
            stmt = (
                delete(VkTgChannel)
                .filter(and_(VkTgChannel.vk_id == vk_id, VkTgChannel.tg_channel == tg_channel))
            )

            session.execute(stmt)
            session.commit()
            return "success"

    @staticmethod
    def update_posts(vk_id: int,
                     tg_channel: str,
                     posts: str):
        with db_helper.engin.connect() as session:
            stmt = (
                update(VkTgChannel)
                .filter(and_(VkTgChannel.vk_id == vk_id, VkTgChannel.tg_channel == tg_channel))
                .values(posts_id=posts, quantity=len(posts.split()))
            )
            session.execute(stmt)
            session.commit()
        return "success"

    @staticmethod
    def clear_inf(counts_post: int) -> str:
        with db_helper.engin.connect() as session:
            query = (
                select(VkTgChannel)
                .filter(VkTgChannel.quantity > counts_post)
            )
            result = session.execute(query)
            posts = result.all()
            for element in map(lambda x: list(x), posts):
                posts_id = list(sorted(element[4].split(), key=lambda x: int(x)))
                clear_posts_id = posts_id[-counts_post:]

                stmt = (
                    update(VkTgChannel)
                    .filter(VkTgChannel.id == element[0])
                    .values(posts_id=" ".join(clear_posts_id), quantity=len(clear_posts_id))
                )

                session.execute(stmt)
                session.commit()

        return "success"


class AdvTable:

    @staticmethod
    def select_adv():
        with db_helper.engin.connect() as session:
            query = (
                select(AdvPosts)
            )

            result = session.execute(query)
            return list(map(lambda el: list(el), result.all()))

    @staticmethod
    def insert_adv(inf_adv: str, date_post: str, tg_vk_posting: str):
        with db_helper.engin.connect() as session:
            new_adv = [{
                "inf_adv": inf_adv,
                "date_post": date_post,
                "tg_vk_posting": tg_vk_posting
            }]

            insert_adv = insert(AdvPosts).values(new_adv)
            session.execute(insert_adv)
            session.commit()
            return "success"

    @staticmethod
    def delete_adv(id_del: int):
        with db_helper.engin.connect() as session:
            del_query = (
                delete(AdvPosts)
                .filter(AdvPosts.id == id_del)
            )

            session.execute(del_query)
            session.commit()

        return "success"

    @staticmethod
    def all_delete_adv():
        with db_helper.engin.connect() as session:
            stmt = delete(AdvPosts)
            session.execute(stmt)
            session.commit()
            return "success"


class TgChannelTable:

    @staticmethod
    def select_channel() -> list[list]:
        with db_helper.engin.connect() as session:
            query = (
                select(TgChannel)
            )
            result = session.execute(query)
        return list(map(lambda el: list(el), result.all()))

    @staticmethod
    def insert_channel(tg_channel: str) -> str:
        with db_helper.engin.connect() as session:
            channel = [{
                "tg_channel": tg_channel
            }]

            insert_tg = insert(TgChannel).values(channel)
            session.execute(insert_tg)
            session.commit()
        return "success"

    @staticmethod
    def delete_channel(tg: str) -> str:
        with db_helper.engin.connect() as session:
            del_query = (
                delete(TgChannel)
                .filter(TgChannel.tg_channel == tg)
            )

            session.execute(del_query)
            session.commit()

        return "success"


