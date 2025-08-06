from vk_api.exceptions import ApiError
from vk_api import VkApi
from src.config import settings
from src.core.query.sql_query import VkTgTable
from loguru import logger
from threading import current_thread


class VkApiRequest:
    def __init__(self, count):
        self.count = count

    def post_information(self, group_id: int, group_tg: str):
        vk = VkApi(token=settings.access_token_vk)
        post_inf = []
        all_message = VkTgTable.select_tg_vk()
        all_message = [[el[1], el[3], el[4]] for el in all_message]
        all_message = [[[vk_id, tg], posts.split()] for vk_id, tg, posts in all_message]
        log_posts = []
        try:
            response = vk.method('wall.get', {
                'owner_id': -group_id,
                'count': self.count,
            })

            posts = response['items']
            if not len(all_message):
                return
            for post in posts:
                if post.get('is_pinned', 0):
                    continue
                id_post = []
                for el in all_message:
                    if el[0][0] == group_id and el[0][1] == group_tg:
                        id_post = el[1]
                if not str(post.get('id', '')) in list(map(str, id_post)):
                    logger.debug(f"post_get: {post.get('id', '')} post_now: {list(map(str, id_post))}")
                    log_posts.extend(list(map(str, id_post)))
                    log_posts.append(str(post.get("id", "")))
                    for el in all_message:
                        if el[0][0] == group_id and el[0][1] == group_tg:
                            el[1].append(str(post.get('id')))
                            lst = sorted(map(int, el[1]))
                            posts = " ".join(list(map(str, lst)))
                            VkTgTable.update_posts(vk_id=el[0][0], tg_channel=el[0][1], posts=posts)
                    text_post = post.get('text', '')
                    list_size_photo = []
                    if 'attachments' in post:
                        for attachments in post.get("attachments", []):
                            if attachments['type'] == 'photo':
                                for count, link in enumerate(attachments['photo']['sizes']):
                                    if count == len(attachments['photo']['sizes']) - 1:
                                        list_size_photo.append(link['url'])
                    post_inf.append([text_post, list_size_photo])

        except ApiError as ex:
            logger.error(f"function: post_information --- {ex}")
            pass

        if list(post_inf):
            logger.info(f"function: post_information"
                        f"group tg: {group_tg},"
                        f" thread: {current_thread().name}"
                        f" group vk: {VkApiRequest.group_all_information(group_id, information='link')},"
                        f"posts: {log_posts}")
        return list(reversed(post_inf))

    @staticmethod
    def group_all_information(group_name, information: str):
        try:
            vk = VkApi(token=settings.access_token_vk)
            response = vk.method('groups.getById', {'group_ids': group_name})
            match information:
                case 'id':
                    return str(response[0].get('id', None))
                case 'name':
                    return response[0].get('name', None)
                case 'link':
                    return f'https://vk.com/{response[0].get("screen_name", None)}'
                case 'screen_name':
                    return response[0].get('screen_name', group_name)
                case _:
                    return response[0]
        except Exception as ex:
            logger.error(f"function: group all information ---- {ex}")

