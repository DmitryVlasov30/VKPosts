from sql_requests import get_db_inf, new_inf, clear_inf, delete_inf, create_main_table, update_inf, create_adv_table, \
    delete_adv_inf, new_adv_inf, delete_all_inf, name_tbl_adv
from filter_adv import filter_add, filter_photo

import vk_api.exceptions
from vk_api import VkApi
from telebot import TeleBot
from telebot.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaVideo
from json import load
from traceback import format_exc
from datetime import datetime
from threading import Timer
from pathlib import Path


from loguru import logger



with open("data.json") as data:
    inf = load(data)
    ACCESS_TOKEN_VK = inf["access_token_vk"]
    TOKEN = inf["token"]
    GENERAL_ADMIN = inf["general_admin"]
    ADMIN_CHAT_ID = inf["moderators"]
    LOG_PATH = Path(inf["path_to_logs"])
    INTERVAL = inf["interval"]

bot = TeleBot(token=TOKEN)
ADMIN_CHAT_ID.append(GENERAL_ADMIN)
flag_stop = False

my_keyboard = []
my_group_for_keyboard = []
status_buttons = {}
inf_adv = ""
text_adv = ""
photo_adv = set()
video_adv = set()
date_adv = ""
message_id_adv = ""

try:

    @logger.catch
    def check_exist_groups(vk, tg) -> str:
        global ACCESS_TOKEN_VK

        flag_vk = False
        flag_tg = False
        vk_session = vk_api.VkApi(token=ACCESS_TOKEN_VK).get_api()
        try:
            vk_session.groups.getById(group_id=vk)
            flag_vk = True
        except vk_api.exceptions.ApiError as ex:
            if ex.code == 100:
                flag_vk = False

        try:
            bot.get_chat(f'@{tg}')
            flag_tg = True
        except Exception as ex:
            if 'Chat not found' in str(ex):
                flag_tg = False
        ans = (flag_vk, flag_tg)
        match ans:
            case (True, False):
                inf_text = "Группы ТГ не существует"
            case (False, False):
                inf_text = "Группы ВК и ТГ не существует"
            case (False, True):
                inf_text = "Группы ВК не существует"
            case _:
                inf_text = "-"
        if inf_text != "-":
            return inf_text
        return ""


    def group_all_information(group_name, information=None):
        global ACCESS_TOKEN_VK
        try:
            vk = vk_api.VkApi(token=ACCESS_TOKEN_VK)
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


    @logger.catch
    def add_inf_message(vk, tg):
        id_group = group_all_information(vk, 'id')

        if id_group is None:
            return False
        inf_db = get_db_inf(name_col="vk_id tg_channel")
        flag_exist = False
        for el in inf_db:
            if el[0] == int(id_group) and el[1] == tg:
                flag_exist = True
        if not flag_exist:
            new_inf(vk_id=int(id_group), vk_screen=vk, tg_channel=tg)
        return flag_exist


    def ignoring_not_admin_message(func):
        def wrapper(message):
            global ADMIN_CHAT_ID
            if not str(message.chat.id) in ADMIN_CHAT_ID:
                return
            function = func(message)
            return function

        return wrapper


    @bot.message_handler(commands=["list_adm"])
    @ignoring_not_admin_message
    @logger.catch
    def adm_list(message) -> None:
        global ADMIN_CHAT_ID
        inf_user = ''
        for el in ADMIN_CHAT_ID:
            chat = bot.get_chat(int(el))
            username = chat.username
            inf_user += f'id: `{el}`, username: `@{username}`\n'
        bot.send_message(message.chat.id, inf_user, parse_mode='Markdown')


    def post_information(group_id: int, group_tg: str):
        global ACCESS_TOKEN_VK
        vk = VkApi(token=ACCESS_TOKEN_VK)
        post_inf = []
        all_message = get_db_inf(name_col="vk_id tg_channel posts_id")
        all_message = [[[vk_id, tg], posts.split()] for vk_id, tg, posts in all_message]
        try:
            response = vk.method('wall.get', {
                'owner_id': -group_id,
                'count': 5
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
                    for el in all_message:
                        if el[0][0] == group_id and el[0][1] == group_tg:
                            el[1].append(str(post.get('id')))
                    text_post = post.get('text', '')
                    list_size_photo = []
                    if 'attachments' in post:
                        for attachments in post['attachments']:
                            if attachments['type'] == 'photo':
                                for count, link in enumerate(attachments['photo']['sizes']):
                                    if count == len(attachments['photo']['sizes']) - 1:
                                        list_size_photo.append(link['url'])
                    post_inf.append([text_post, list_size_photo])

        except vk_api.exceptions.ApiError as ex:
            logger.error(f"function: post_information --- {ex}")
            pass

        id_posts = ""
        for el in all_message:
            el[1] = sorted(map(int, el[1]))
            posts = " ".join(list(map(str, el[1])))
            if int(el[0][0]) == group_id and str(el[0][1]) == group_tg:
                id_posts = posts
            update_inf(el[0][0], el[0][1], posts)
        if list(post_inf):
            logger.info(f"function: post_information"
                        f"group tg: {group_tg},"
                        f" group vk: {group_all_information(group_id, information='link')},"
                        f" posts: {id_posts}")
        return list(reversed(post_inf))


    @bot.message_handler(commands=["start"])
    @logger.catch
    def main(message) -> None:
        global LOG_PATH
        text_message = ('Вы запустили бота для сборки и пересылки информации из ВКонтакте в Телеграм\n'
                        'Используйте команду /help для вызова списка функций\n\n'
                        '<em><u><i>Сreated by Vlasov</i></u></em>\n'
                        'GitHub -> https://github.com/DmitryVlasov30')
        bot.send_message(message.chat.id, text_message, parse_mode='html')

        start_timer(message)
        create_main_table()
        create_adv_table()
        logger.add(LOG_PATH,
                   rotation="10 MB",
                   compression="zip",
                   level="DEBUG")
        logger.info("была использованна функция main")


    if not flag_stop:
        @logger.catch
        def start_timer(message):
            global INTERVAL
            Timer(INTERVAL, message_post, args=(message,)).start()


    @bot.message_handler(commands=["add"])
    @ignoring_not_admin_message
    def add_vk_tg_group(message) -> None:
        chat = message.chat.id
        try:
            vk, tg = message.text[4:].strip().split()
            if 'https://vk.com' in vk:
                vk = vk.split('/')[-1]

            if 'https://t.me' in tg:
                tg = tg.split('/')[-1]

            if '@' in tg:
                tg = tg.replace('@', '')
            inf_exist = check_exist_groups(vk, tg)
            if inf_exist != "-" and inf_exist != "":
                bot.send_message(chat, inf_exist)
                return

            vk = group_all_information(vk, 'screen_name')
            text = add_inf_message(vk, tg)

            if text:
                bot.send_message(chat, 'Группa уже отслеживается')
                return
            bot.send_message(chat, 'Группa отслеживается')
            logger.info("была успешно использованна фукция add_vk_tg_group")
        except Exception as ex:
            logger.error(f'Произошла ошибка: {ex} в функции add_vk_tg_group')
            bot.send_message(chat, f'Произошла ошибка: {ex} в функции add_vk_tg_group')


    @bot.message_handler(commands=['del'])
    @ignoring_not_admin_message
    def del_group(message) -> None:
        chat = message.chat.id
        try:
            all_inf = get_db_inf(name_col="vk_screen tg_channel")

            vk, tg = message.text[4:].strip().split()

            if 'https://vk.com' in vk:
                vk = vk.split('/')[-1]

            if 'https://t.me' in tg:
                tg = tg.split('/')[-1]

            if '@' in tg:
                tg = tg.replace('@', '')

            flag_exists = False
            for vk_db, tg_db in all_inf:
                if vk_db == vk and tg_db == tg:
                    flag_exists = True
            if not flag_exists:
                bot.send_message(chat, 'Группа не найдена')
                return

            vk = group_all_information(vk, "id")
            text_otv = delete_inf(vk, tg)

            if text_otv != "":
                bot.send_message(chat, text_otv)
                return
            bot.send_message(chat, 'Группа удалена')
        except Exception as ex:
            logger.error(f"Произошла ошибка: {ex} в функции del_group")
            bot.send_message(chat, f'Произошла ошибка: {ex} в функции del_group')


    if not flag_stop:
        @logger.catch
        def message_post(message):
            global ADMIN_CHAT_ID

            try:
                group_inf = get_db_inf(name_col="vk_screen tg_channel vk_id")

                if len(group_inf) == 0:
                    start_timer(message)
                    return

                for vk, tg, id_group_vk in group_inf:
                    new_posts = post_information(id_group_vk, tg)
                    if new_posts is None:
                        for admin in ADMIN_CHAT_ID:
                            bot.send_message(admin, "функция post_information вернула None")
                            logger.error("функция post_information вернула None")
                        return

                    count_id = 0
                    for text_post, photo_post in new_posts:
                        try:
                            if filter_photo(vk):
                                photo_post = []

                            if text_post == '' and len(photo_post) > 1:
                                media = [InputMediaPhoto(media=url) for url in photo_post]
                                bot.send_media_group(chat_id=f'@{tg}', media=media)
                            elif len(photo_post) == 1 and text_post == '':
                                bot.send_photo(f'@{tg}', photo=photo_post[0])
                            elif text_post != '' and len(photo_post) > 1 and filter_add(text_post):
                                media = []
                                for i, url in enumerate(photo_post):
                                    if i == 0:
                                        media.append(InputMediaPhoto(media=url, caption=text_post))
                                        continue
                                    media.append(InputMediaPhoto(media=url))
                                bot.send_media_group(chat_id=f'@{tg}', media=media)
                            elif text_post != '' and len(photo_post) == 1 and filter_add(text_post):
                                bot.send_photo(f'@{tg}', photo_post[0], caption=text_post)
                            elif len(photo_post) == 0 and text_post != '' and filter_add(text_post):
                                bot.send_message(f'@{tg}', text_post)
                            elif len(photo_post) == 0 and text_post == '':
                                continue

                            count_id += 1
                        except Exception as ex:
                            for el in ADMIN_CHAT_ID:
                                logger.error(f'Произошла ошибка: {ex} в функции message_post. VK: {vk}, TG: {tg}')
                                bot.send_message(el,
                                    f'Произошла ошибка: {ex} в функции message_post. VK: {vk}, TG: {tg}'
                                )
                            continue
                    if count_id != len(new_posts):
                        logger.debug(f"количество опубликованных постов не равно количеству пришедших постов в VK: {vk}, TG: {tg}")

            except Exception as ex:
                logger.error(f'Произошла ошибка: {ex} в функции message_post')
                for el in ADMIN_CHAT_ID:
                    bot.send_message(el, f'Произошла ошибка: {ex} в функции message_post')
            finally:
                clear_inf(15)
                ready_adv = del_adv()
                send_adv_posts(ready_adv)
                start_timer(message)
                return


    @bot.message_handler(commands=["group"])
    @ignoring_not_admin_message
    @logger.catch
    def get_group_list(message) -> None:
        all_inf = get_db_inf(name_col="vk_screen tg_channel vk_id")

        if len(all_inf) == 0:
            bot.send_message(message.chat.id, "У вас нет групп")
            return

        inf_group = 'Ваши группы:\n'
        for vk, tg, id_vk in all_inf:
            vk_name = group_all_information(id_vk, 'screen_name')
            vk_link = f'https://vk.com/{vk_name}'
            inf_group += (f'*VK*: `{vk_name}`\n'
                          f'*TG*: `{tg}`\n'
                          f'*[LINK]({vk_link})*\n\n')
        bot.send_message(message.chat.id, inf_group, parse_mode='MarkdownV2', disable_web_page_preview=True)
        logger.info("была использованна функция get_group_list")


    @bot.message_handler(commands=['help'])
    @ignoring_not_admin_message
    @logger.catch
    def help_func(message) -> None:
        message_text = ('/start -> перезапускает интервал проверки постов из ВК и выводит начальную информацию\n'
                        '/add("ссылка на паблик в вк" "username вашего тг канала") -> добавляет канал и тг для пересылки постов\n'
                        '/del("название из ссылки на паблик в вк" "username вашего тг канала") -> удалит канал и тг для пересылки постов\n'
                        '/group -> выводит список ваших тг и вк каналов\n'
                        '/list_adm -> возвращает список админов\n'
                        '/new_adm("chat id") -> добавляет админа в список\n'
                        '/del_adm("chat id или username") -> удаляет админа\n'
                        '/stop -> останавливает бота\n'
                        '/my_id -> выводит ваш chat id')
        bot.send_message(message.chat.id, message_text)
        logger.info("использованна функция help_func")


    @bot.message_handler(commands=["my_id"])
    def my_id(message) -> None:
        bot.send_message(message.chat.id, f'Ваш id: `{str(message.chat.id)}`', parse_mode='Markdown')


    @bot.message_handler(commands=["stop"])
    @ignoring_not_admin_message
    @logger.catch
    def stop_bot(message) -> None:
        global ADMIN_CHAT_ID, flag_stop
        for el in ADMIN_CHAT_ID:
            bot.send_message(el, 'Работа бота завершена')
        flag_stop = True
        bot.stop_bot()
        logger.info("использованна функция остановки бота")
        exit(0)


    @bot.message_handler(commands=["my_adv"])
    @ignoring_not_admin_message
    @logger.catch
    def get_adv_inf(message):
        all_inf = get_db_inf(name_table=name_tbl_adv)
        if not len(all_inf):
            bot.send_message(message.chat.id, "У вас нет рекламы")
            return

        for el in all_inf:
            adv_text_inf, adv_photo_inf, adv_video_inf = el[1].split("/")
            send_adv_message_submit(
                chat_id=message.chat.id,
                video=adv_video_inf,
                photo=adv_photo_inf,
                text=adv_text_inf,
                local_func=True
            )
            text = (f"информация о вашей рекламе:\n"
                    f"<b>id</b>: {el[0]}\n"
                    f"<b>Дата публикации</b>:  {el[2]}\n"
                    f"<b>каналы куда пойдет рассылка</b>: \n{'\n'.join(el[3].split("/"))}\n")
            bot.send_message(message.chat.id, text, parse_mode='html')
            logger.info("использованна функция get_adv_inf")


    @bot.message_handler(commands=["delet_db"])
    @ignoring_not_admin_message
    @logger.catch
    def reset_all_data(message):
        delete_all_inf()
        logger.info("использованна функция delet_db")
        bot.send_message(message.chat.id, "реклама отчищена")


    @bot.message_handler(commands=["reset"])
    @logger.catch
    def reset_adv_inf(message, flag_message=True):
        global my_keyboard, my_group_for_keyboard, status_buttons, inf_adv, text_adv, photo_adv, video_adv, date_adv, \
            message_id_adv
        my_keyboard = []
        my_group_for_keyboard = []
        status_buttons = {}
        inf_adv = ""
        text_adv = ""
        photo_adv = set()
        video_adv = set()
        date_adv = ""
        message_id_adv = ""
        if flag_message:
            bot.send_message(message.chat.id, "вся информация про рекламу отчищена")
        logger.info("использованна функция reset")


    @logger.catch
    def add_submit(call) -> None:
        global my_keyboard, my_group_for_keyboard

        call_data = call.data.split()
        tg, action = call_data[0], call_data[1]
        new_marcup = InlineKeyboardMarkup(row_width=1)
        for i, el in enumerate(my_group_for_keyboard):
            if el == tg:
                status_buttons[el] = "not"
                my_keyboard[i] = InlineKeyboardButton(text=f"✅{tg}", callback_data=f"{tg} not")
        new_marcup.add(*my_keyboard)
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=new_marcup
        )


    @logger.catch
    def del_submit(call) -> None:
        global my_keyboard, my_group_for_keyboard

        call_data = call.data.split()
        tg, action = call_data[0], call_data[1]
        new_marcup = InlineKeyboardMarkup(row_width=1)
        for i, el in enumerate(my_group_for_keyboard):
            if el == tg:
                status_buttons[el] = "add"
                my_keyboard[i] = InlineKeyboardButton(text=f"{tg}", callback_data=f"{tg} add")
        new_marcup.add(*my_keyboard)
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=new_marcup
        )
        logger.info("использованна функция del_submit")


    @logger.catch
    def save_submit(call):
        global my_keyboard, my_group_for_keyboard, inf_adv, photo_adv, video_adv, text_adv, status_buttons, date_adv

        inf_adv = (f"{text_adv if text_adv else '-'}"
                   f"/{' '.join([el for el in photo_adv]) if photo_adv else '-'}/"
                   f"{' '.join(el for el in video_adv) if video_adv else '-'}")
        photo_adv = set()
        video_adv = set()
        list_group = ""
        for tg in my_group_for_keyboard:
            if status_buttons[tg] == "not":
                list_group += f"{tg}/"
        new_adv_inf(inf_adv=inf_adv, date_post=date_adv, tg_vk_posting=list_group)
        bot.send_message(call.message.chat.id, "реклама сохраненна")
        logger.info("использованна функция save_submit")
        return


    def del_adv() -> list:
        all_adv = get_db_inf(name_table=name_tbl_adv)
        ready_adv = []
        for el in all_adv:
            if time_difference(el[2]) == -1:
                ready_adv.append(el)
                delete_adv_inf(el[0])
        return ready_adv


    @logger.catch
    def send_adv_posts(adv_lst: list) -> None:
        for adv in adv_lst:
            adv_text_inf, adv_photo_inf, adv_video_inf = adv[1].split("/")
            group_post_adv = [tg for tg in adv[3].split("/") if tg != '']
            for tg in group_post_adv:
                send_adv_message_submit(
                    chat_id=f"@{tg}",
                    video=adv_video_inf,
                    photo=adv_photo_inf,
                    text=adv_text_inf,
                    local_func=True
                )
            logger.info("использованна функция send_adv_posts")



    @bot.callback_query_handler(func=lambda call: True)
    @logger.catch
    def callback(call):
        match call.data.split()[-1]:
            case "add":
                add_submit(call)
            case "not":
                del_submit(call)
            case "end":
                save_submit(call)


    @logger.catch
    def inf_post_adv(message) -> tuple:
        message_text = message.text
        if message_text is None or message_text[:4].strip() != "/adv":
            return ()
        message_text = message_text[1:]
        idx_start = message_text.find("/") + 1
        idx_end = message_text[idx_start:].find("/") + idx_start
        date = message_text[idx_start:idx_end]
        text_adv_inf = message_text[idx_end + 1:].strip()

        return date, text_adv_inf


    @bot.message_handler(content_types=["video", "photo"])
    @logger.catch
    def add_video_photo(message) -> None:
        global video_adv, photo_adv, text_adv
        match message.content_type:
            case "video":
                video_adv.add(message.video.file_id)
            case "photo":
                photo_adv.add(message.photo[-1].file_id)


    @logger.catch
    def time_difference(input_time):
        try:
            given_time = datetime.strptime(input_time, "%H:%M %d.%m.%Y")
        except ValueError:
            logger.info("Неверный формат времени в функции time_defference")
            return "Неверный формат времени. Используйте 'часы:минуты день.месяц.год'."
        current_time = datetime.now()
        current_time, given_time = given_time, current_time
        if current_time >= given_time:
            difference = current_time - given_time

            days = difference.days
            hours, remainder = divmod(difference.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            seconds = days * 24 * 60 * 60 + hours * 60 * 60 + minutes * 60
            return {
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "seconds_diff": seconds,
            }
        else:
            return -1


    def send_adv_message_submit(chat_id, photo="-", video="-", text="-", local_func=False):
        global photo_adv, video_adv, text_adv
        try:
            if not local_func:
                photo_loc = photo_adv
                video_loc = video_adv
                text_loc = text_adv
            else:
                photo_loc = photo.split() if photo != "-" else []
                video_loc = video.split() if video != "-" else []
                text_loc = text if text != "-" else ""
            list_photo = []
            list_video = []
            media_all = []
            if text_loc == "":
                if len(photo_loc) >= 1:
                    list_photo = [InputMediaPhoto(media=photo_id) for photo_id in photo_loc]
                if len(video_loc) >= 1:
                    list_video = [InputMediaVideo(media=video_id) for video_id in video_loc]

                if len(list_video) > 1 or len(list_photo) > 1:
                    media_all.extend(list_video)
                    media_all.extend(list_photo)

                if len(video_loc) + len(photo_loc) > 1:
                    bot.send_media_group(chat_id=chat_id, media=media_all)
                else:
                    if len(photo_loc) == 1 and len(video_loc) == 0:
                        list_photo = [el for el in photo_loc]
                        bot.send_photo(chat_id=chat_id, photo=list_photo[0])
                    if len(video_loc) == 1 and len(photo_loc) == 0:
                        list_video = [el for el in video_loc]
                        bot.send_video(chat_id=chat_id, video=list_video[0])
            else:
                if len(photo_loc) == 0 and len(video_loc) == 0:
                    bot.send_message(chat_id=chat_id, text=text_loc)
                if len(video_loc) != 0 and len(photo_loc) != 0:
                    for i, el in enumerate(video_loc):
                        if i == 0:
                            list_video.append(InputMediaVideo(media=el, caption=text_loc))
                            continue
                        list_video.append(InputMediaVideo(media=el))
                    list_photo = [InputMediaPhoto(media=el) for el in photo_loc]
                elif len(photo_loc) > 1 and len(video_loc) == 0:
                    for i, el in enumerate(photo_loc):
                        if i == 0:
                            list_photo.append(InputMediaPhoto(media=el, caption=text_loc))
                            continue
                        list_photo.append(InputMediaPhoto(media=el))
                elif len(video_loc) > 1 and len(photo_loc) == 0:
                    for i, el in enumerate(video_loc):
                        if i == 0:
                            list_video.append(InputMediaVideo(media=el, caption=text_loc))
                            continue
                        list_video.append(InputMediaVideo(media=el))

                if len(video_loc) + len(photo_loc) > 1:
                    media_all.extend(list_photo)
                    media_all.extend(list_video)
                    bot.send_media_group(chat_id=chat_id, media=media_all)
                else:
                    if len(photo_loc) == 1 and len(video_loc) == 0:
                        list_photo = [el for el in photo_loc]
                        bot.send_photo(chat_id=chat_id, photo=list_photo[0], caption=text_loc)
                    if len(video_loc) == 1 and len(photo_loc) == 0:
                        list_video = [el for el in video_loc]
                        bot.send_video(chat_id=chat_id, video=list_video[0], caption=text_loc)

        except Exception as ex:
            logger.error(f"ошибка в функции send_adv_message: {ex}")


    @bot.message_handler(content_types=["text"])
    @ignoring_not_admin_message
    def adv_newsletter(message) -> None:
        global my_keyboard, my_group_for_keyboard, status_buttons, text_adv, date_adv, message_id_adv, photo_adv, video_adv
        date_adv_text = inf_post_adv(message)
        if not date_adv_text:
            bot.send_message(message.chat.id, "вы ввели что-то не так")
            logger.info("введен неизвестный текст в функции adv_newsletter")
            return

        date = time_difference(date_adv_text[0])
        date_adv = date_adv_text[0]
        if not type(date) is dict:
            reset_adv_inf(message, flag_message=False)
            text = ""
            if type(date) is int:
                text = "вы ввели дату, которая меньше нынешней"
            if type(date) is str:
                text = date
            bot.send_message(message.chat.id, text)
            return

        try:
            vk_public = get_db_inf(name_col="tg_channel vk_screen")
            markup = InlineKeyboardMarkup(row_width=1)
            my_keyboard = []
            my_group_for_keyboard = []
            status_buttons = {}
            text_adv = date_adv_text[1]
            tg_channel = set(el[0] for el in vk_public)
            for tg in tg_channel:
                status_buttons[tg] = "add"
                my_group_for_keyboard.append(tg)
                my_keyboard.append(InlineKeyboardButton(f"{tg}", callback_data=f"{tg} add"))

            my_keyboard.append(InlineKeyboardButton(f"подтвердить", callback_data="end"))
            markup.add(*my_keyboard)
            bot.send_message(message.chat.id, "вот ваше сообщение:")
            send_adv_message_submit(message.chat.id)
            message_text = "Выберите каналы, в которые должна пойти рассылка"
            bot.send_message(message.chat.id, message_text, reply_markup=markup)

            logger.info("использованна функция adv_newsletter")

        except Exception as ex:
            logger.error(f"{ex} (error)!")
            bot.send_message(message.chat.id, f'Произошла ошибка: {ex} в функции adv_newsletter')


except:
    logger.error(f"{format_exc()}")


print('bot worked')
bot.infinity_polling(timeout=10, long_polling_timeout=150)
logger.info("бот остановлен")