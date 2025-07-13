from sqlalchemy import text, insert, select, func, cast, and_, delete

from src.core.models.db_helper import db_helper
from src.core.models.models import VkTgChannel, AdvPosts, TgChannel
from src.core.models.base import Base


async def create_table():
    async with db_helper.engin.begin() as connect:
        await connect.run_sync(Base.metadata.create_all)


# доработать функцию get
async def clear_inf(counts_post: int):
    async with db_helper.engin.connect() as session:
        query = (
            select(VkTgChannel)
            .filter(VkTgChannel.quantity > counts_post)
        )
        result = await session.execute(query)
        posts = result.all()
        print(posts)
        for element in map(lambda x: list(x), posts):
            posts_id = list(sorted(element[4].split(), key=lambda x: int(x)))
            clear_posts_id = posts_id[-counts_post:]

            quantity = len(clear_posts_id)
            element[4] = " ".join(clear_posts_id)
            element[5] = str(quantity)

            del_el = delete(VkTgChannel).filter(VkTgChannel.id == int(element[0]))
            await session.execute(del_el)

            data = [{
                "id": element[0],
                "vk_id": element[1],
                "vk_screen": element[2],
                "tg_channel": element[3],
                "posts_id": element[4],
                "quantity": element[5],
            }]

            await session.execute(insert(VkTgChannel).values(data))

        await session.commit()

    return "success"


async def new_tg_vk(vk_id: int,
                    vk_screen: str,
                    tg_channel: str,
                    posts: str):
    async with db_helper.engin.connect() as session:
        new_inf = [{"vk_id": vk_id,
                    "vk_screen": vk_screen,
                    "tg_channel": tg_channel,
                    "posts_id": posts,
                    "quantity": len(posts.split())
                    }]
        ins = insert(VkTgChannel).values(new_inf)
        await session.execute(ins)
        await session.commit()
        print("success")


async def delete_tg_vk(vk_id: int, tg_channel: str):
    async with db_helper.engin.connect() as session:
        del_query = (
            delete(VkTgChannel)
            .filter(and_(VkTgChannel.vk_id == vk_id, VkTgChannel.tg_channel == tg_channel))
        )

        await session.execute(del_query)
        await session.commit()
        return "success"


async def select_tg_vk():
    async with db_helper.engin.connect() as session:
        query = (
            select(VkTgChannel)
        )

        result = await session.execute(query)
        return result.all()


async def update_posts(
        vk_id: int,
        tg_channel: str,
        posts: str):
    async with db_helper.engin.connect() as session:
        query = (
            select(VkTgChannel)
            .filter(and_(VkTgChannel.vk_id == vk_id, VkTgChannel.tg_channel == tg_channel))
        )
        pab = await session.execute(query)
        pab = list(pab.all()[0])
        del_query = delete(VkTgChannel).filter(VkTgChannel.id == pab[0])
        await session.execute(del_query)

        new_data = [{
            "id": pab[0],
            "vk_id": pab[1],
            "vk_screen": pab[2],
            "tg_channel": pab[3],
            "posts_id": posts,
            "quantity": len(posts.split())
        }]

        await session.execute(insert(VkTgChannel).values(new_data))
        await session.commit()

    return "success"


async def add_adv(inf_adv: str, date_post: str, tg_vk_posting: str):
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


async def delete_adv(id_del: int):
    async with db_helper.engin.connect() as session:
        del_query = (
            delete(AdvPosts)
            .filter(AdvPosts.id == id_del)
        )

        await session.execute(del_query)
        await session.commit()
        return "success"


async def insert_channel(tg_channel: str):
    async with db_helper.engin.connect() as session:
        channel = [{
            "tg_channel": tg_channel
        }]

        insert_tg = insert(TgChannel).values(channel)
        await session.execute(insert_tg)
        await session.commit()
        return "success"


async def delete_channel(tg: str):
    async with db_helper.engin.connect() as session:
        del_query = (
            delete(TgChannel)
            .filter(TgChannel.tg_channel == tg)
        )

        await session.execute(del_query)
        await session.commit()


async def select_adv():
    async with db_helper.engin.connect() as session:
        query = (
            select(AdvPosts)
        )

        result = await session.execute(query)
        return result.all()


async def select_channel():
    async with db_helper.engin.connect() as session:
        query = (
            select(TgChannel)
        )

        result = await session.execute(query)
        return result.all()

