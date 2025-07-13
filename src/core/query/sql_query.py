from sqlalchemy import insert, select, and_, delete, update

from src.core.models.db_helper import db_helper
from src.core.models.models import VkTgChannel, AdvPosts, TgChannel
from src.core.models.base import Base


async def create_table():
    async with db_helper.engin.begin() as connect:
        await connect.run_sync(Base.metadata.create_all)


class VkTgTable:

    @staticmethod
    async def select_tg_vk() -> list:
        async with db_helper.engin.connect() as session:
            query = (
                select(VkTgChannel)
            )

            result = await session.execute(query)
            return list(map(lambda el: list(el), result.all()))

    @staticmethod
    async def insert_tg_vk(vk_id: int,
                           vk_screen: str,
                           tg_channel: str,
                           posts: str = "") -> str:
        async with db_helper.engin.connect() as session:
            new_inf = [{
                "vk_id": vk_id,
                "vk_screen": vk_screen,
                "tg_channel": tg_channel,
                "posts_id": posts,
                "quantity": len(posts.split())
            }]
            stmt = insert(VkTgChannel).values(new_inf)
            await session.execute(stmt)
            await session.commit()
            return "success"

    @staticmethod
    async def delete_tg_vk(vk_id: int, tg_channel: str) -> str:
        async with db_helper.engin.connect() as session:
            stmt = (
                delete(VkTgChannel)
                .filter(and_(VkTgChannel.vk_id == vk_id, VkTgChannel.tg_channel == tg_channel))
            )

            await session.execute(stmt)
            await session.commit()
            return "success"

    @staticmethod
    async def update_posts(vk_id: int,
                           tg_channel: str,
                           posts: str):
        async with db_helper.engin.connect() as session:
            stmt = (
                update(VkTgChannel)
                .filter(and_(VkTgChannel.vk_id == vk_id, VkTgChannel.tg_channel == tg_channel))
                .values(posts_id=posts, quantity=len(posts.split()))
            )
            await session.execute(stmt)
            await session.commit()
        return "success"

    @staticmethod
    async def clear_inf(counts_post: int) -> str:
        async with db_helper.engin.connect() as session:
            query = (
                select(VkTgChannel)
                .filter(VkTgChannel.quantity > counts_post)
            )
            result = await session.execute(query)
            posts = result.all()
            for element in map(lambda x: list(x), posts):
                posts_id = list(sorted(element[4].split(), key=lambda x: int(x)))
                clear_posts_id = posts_id[-counts_post:]

                stmt = (
                    update(VkTgChannel)
                    .filter(VkTgChannel.id == element[0])
                    .values(posts_id=" ".join(clear_posts_id), quantity=len(clear_posts_id))
                )

                await session.execute(stmt)

            await session.commit()

        return "success"


class AdvTable:

    @staticmethod
    async def select_adv():
        async with db_helper.engin.connect() as session:
            query = (
                select(AdvPosts)
            )

            result = await session.execute(query)
            return list(map(lambda el: list(el), result.all()))

    @staticmethod
    async def insert_adv(inf_adv: str, date_post: str, tg_vk_posting: str):
        async with db_helper.engin.connect() as session:
            new_adv = [{
                "inf_adv": inf_adv,
                "date_post": date_post,
                "tg_vk_posting": tg_vk_posting
            }]

            insert_adv = insert(AdvPosts).values(new_adv)
            await session.execute(insert_adv)
            await session.commit()
            return "success"

    @staticmethod
    async def delete_adv(id_del: int):
        async with db_helper.engin.connect() as session:
            del_query = (
                delete(AdvPosts)
                .filter(AdvPosts.id == id_del)
            )

            await session.execute(del_query)
            await session.commit()

        return "success"

    @staticmethod
    async def all_delete_adv():
        async with db_helper.engin.connect() as session:
            stmt = delete(AdvPosts)
            await session.execute(stmt)
            await session.commit()
            return "success"


class TgChannelTable:

    @staticmethod
    async def select_channel() -> list[list]:
        async with db_helper.engin.connect() as session:
            query = (
                select(TgChannel)
            )
            result = await session.execute(query)
        return list(map(lambda el: list(el), result.all()))

    @staticmethod
    async def insert_channel(tg_channel: str) -> str:
        async with db_helper.engin.connect() as session:
            channel = [{
                "tg_channel": tg_channel
            }]

            insert_tg = insert(TgChannel).values(channel)
            await session.execute(insert_tg)
            await session.commit()
        return "success"

    @staticmethod
    async def delete_channel(tg: str) -> str:
        async with db_helper.engin.connect() as session:
            del_query = (
                delete(TgChannel)
                .filter(TgChannel.tg_channel == tg)
            )

            await session.execute(del_query)
            await session.commit()

        return "success"
