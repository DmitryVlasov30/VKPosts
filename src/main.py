from src.utils import FilterAdv, AdvFormat, Checker, ignoring_not_admin_message
from src.core.query.sql_query import VkTgTable, AdvTable, TgChannelTable, create_table
from vk_api_req.request import VkApiRequest
from config import settings

import time
from telebot import TeleBot
from telebot.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaVideo
from traceback import format_exc
from datetime import datetime
from threading import current_thread, main_thread, Thread

from loguru import logger

logger.add(settings.path_to_logs, level="DEBUG")

bot = TeleBot(token=settings.token_tg)
ADMIN_CHAT_ID = settings.moderators
ADMIN_CHAT_ID.append(settings.general_admin)
flag_stop = False
my_keyboard = []
my_group_for_keyboard = []
status_buttons = {}
inf_adv = ""
text_adv = ""
photo_adv, video_adv = set(), set()
date_adv = ""
message_id_adv = ""

try:
    @logger.catch
    def add_inf_message(vk, tg):
        id_group = VkApiRequest.group_all_information(vk, 'id')

        if id_group is None:
            return False
        inf_db = [[el[1], el[3]] for el in VkTgTable.select_tg_vk()]
        flag_exist = False
        for el in inf_db:
            if el[0] == int(id_group) and el[1] == tg:
                flag_exist = True
        if not flag_exist:
            VkTgTable.insert_tg_vk(vk_id=int(id_group), vk_screen=vk, tg_channel=tg)
        return flag_exist


    @bot.message_handler(commands=["list_adm"])
    @ignoring_not_admin_message
    @logger.catch
    def adm_list(message) -> None:
        inf_user = ''
        for el in ADMIN_CHAT_ID:
            chat = bot.get_chat(int(el))
            username = chat.username
            inf_user += f'id: `{el}`, username: `@{username}`\n'
        bot.send_message(message.chat.id, inf_user, parse_mode='Markdown')


    @bot.message_handler(commands=["start"])
    @logger.catch
    def main(message) -> None:
        text_message = ('Вы запустили бота для сборки и пересылки информации из ВКонтакте в Телеграм\n'
                        'Используйте команду /help для вызова списка функций\n\n'
                        '<em><u><i>Created by Vlasov</i></u></em>')
        bot.send_message(message.chat.id, text_message, parse_mode='html')

        thread = Thread(target=start_timer, daemon=True, args=(message,))
        thread.start()
        create_table()
        logger.info("была использована функция main")


    if not flag_stop:
        @logger.catch
        def start_timer(message):
            while True:
                time.sleep(settings.interval)
                logger.debug("test")
                message_post(message)


    def processing_input_data(text: str):
        vk, tg = text[4:].strip().split()
        if 'https://vk.com' in vk:
            vk = vk.split('/')[-1]

        if 'https://t.me' in tg:
            tg = tg.split('/')[-1]

        if '@' in tg:
            tg = tg.replace('@', '')

        return vk, tg


    @bot.message_handler(commands=["add"])
    @ignoring_not_admin_message
    def add_vk_tg_group(message) -> None:
        chat = message.chat.id
        try:
            vk, tg = processing_input_data(message.text)

            checker = Checker(bot)
            inf_exist = checker.check_exist_groups(vk, tg)
            if inf_exist != "-" and inf_exist != "":
                bot.send_message(chat, inf_exist)
                return

            vk = VkApiRequest.group_all_information(vk, 'screen_name')
            text = add_inf_message(vk, tg)

            if text:
                bot.send_message(chat, 'Группa уже отслеживается')
                return
            bot.send_message(chat, 'Группa отслеживается')
            logger.info(f"была успешно использована функция пользователем c id {chat}")
        except Exception as ex:
            logger.error(f'Произошла ошибка: {ex} в функции add_vk_tg_group')
            bot.send_message(chat, f'Произошла ошибка: {ex} в функции add_vk_tg_group')


    @bot.message_handler(commands=['del'])
    @ignoring_not_admin_message
    def del_group(message) -> None:
        chat = message.chat.id
        try:
            all_inf = [[el[2], el[3]] for el in VkTgTable.select_tg_vk()]

            vk, tg = processing_input_data(message.text)

            logger.debug(all_inf)
            flag_exists = False
            for vk_db, tg_db in all_inf:
                if vk_db == vk and tg_db == tg:
                    flag_exists = True
            if not flag_exists:
                bot.send_message(chat, 'Группа не найдена')
                return

            vk = VkApiRequest.group_all_information(vk, "id")
            text_otv = VkTgTable.delete_tg_vk(vk, tg)

            if text_otv != "success":
                bot.send_message(chat, text_otv)
                return
            bot.send_message(chat, 'Группа удалена')
            logger.info(f"успешно использована функция пользователем c id {chat}")
        except Exception as ex:
            logger.error(f"Произошла ошибка: {ex} в функции del_group")
            bot.send_message(chat, f'Произошла ошибка: {ex} в функции del_group')


    if not flag_stop:
        @logger.catch
        def message_post(message):

            try:
                group_inf = [[el[2], el[3], el[1]] for el in VkTgTable.select_tg_vk()]

                if len(group_inf) == 0:
                    start_timer(message)
                    return

                for vk, tg, id_group_vk in group_inf:
                    new_posts = VkApiRequest(5).post_information(id_group_vk, tg)
                    if new_posts is None:
                        for admin in ADMIN_CHAT_ID:
                            bot.send_message(admin, "функция post_information вернула None")
                            logger.error("функция post_information вернула None")
                        return

                    count_id = 0
                    for text_post, photo_post in new_posts:
                        try:
                            if FilterAdv.filter_photo(vk):
                                photo_post = []

                            text_post = FilterAdv.replace_warning_word(text_post, tg)
                            logger.info(text_post if text_post != "" else "текст не найден")

                            if text_post == '' and len(photo_post) > 1:
                                media = [InputMediaPhoto(media=url) for url in photo_post]
                                bot.send_media_group(chat_id=f'@{tg}', media=media)
                            elif len(photo_post) == 1 and text_post == '':
                                bot.send_photo(f'@{tg}', photo=photo_post[0])
                            elif text_post != '' and len(photo_post) > 1 and FilterAdv.filter_add(text_post):
                                media = []
                                for i, url in enumerate(photo_post):
                                    if i == 0:
                                        media.append(InputMediaPhoto(media=url, caption=text_post))
                                        continue
                                    media.append(InputMediaPhoto(media=url))
                                bot.send_media_group(chat_id=f'@{tg}', media=media)
                            elif text_post != '' and len(photo_post) == 1 and FilterAdv.filter_add(text_post):
                                bot.send_photo(f'@{tg}', photo_post[0], caption=text_post)
                            elif len(photo_post) == 0 and text_post != '' and FilterAdv.filter_add(text_post):
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
                        logger.debug(
                            f"количество опубликованных постов не равно количеству пришедших постов: VK: {vk}, TG: {tg}"
                        )

            except Exception as ex:
                logger.error(f'Произошла ошибка: {ex} в функции message_post')
                for el in ADMIN_CHAT_ID:
                    bot.send_message(el, f'Произошла ошибка: {ex} в функции message_post')
            finally:
                flag = VkTgTable.clear_inf(15)
                logger.info(flag)
                ready_adv = del_adv()
                send_adv_posts(ready_adv)
                return


    @bot.message_handler(commands=["group"])
    @ignoring_not_admin_message
    @logger.catch
    def get_group_list(message) -> None:
        all_inf = [[el[2], el[3], el[1]] for el in VkTgTable.select_tg_vk()]
        logger.debug(all_inf)
        if len(all_inf) == 0:
            bot.send_message(message.chat.id, "У вас нет групп")
            return

        inf_group = 'Ваши группы:\n'
        for vk, tg, id_vk in all_inf:
            vk_name = VkApiRequest.group_all_information(id_vk, 'screen_name')
            vk_link = f'https://vk.com/{vk_name}'
            inf_group += (f'*VK*: `{vk_name}`\n'
                          f'*TG*: `{tg}`\n'
                          f'*[LINK]({vk_link})*\n\n')
        bot.send_message(message.chat.id, inf_group, parse_mode='MarkdownV2', disable_web_page_preview=True)
        logger.info(f"была использована функция пользователем c id {message.chat.id}")


    @bot.message_handler(commands=['help'])
    @ignoring_not_admin_message
    @logger.catch
    def help_func(message) -> None:
        message_text = ('/start -> перезапускает интервал проверки постов из ВК и выводит начальную информацию\n'
                        '/add("ссылка на паблик в вк" "username вашего тг канала") -> добавляет канал и тг для '
                        'пересылки постов\n'
                        '/del("название из ссылки на паблик в вк" "username вашего тг канала") -> удалит канал и тг '
                        'для пересылки постов\n'
                        '/group -> выводит список ваших тг и вк каналов\n'
                        '/list_adm -> возвращает список админов\n'
                        '/new_adm("chat id") -> добавляет админа в список\n'
                        '/del_adm("chat id или username") -> удаляет админа\n'
                        '/stop -> останавливает бота\n'
                        '/my_id -> выводит ваш chat id\n'
                        '/adv(дата рассылки в формате: /час:время день.месяц.год/, после написания даты, '
                        'нужно указать текст рассылки, но до вызова функции нужно отправить видео и фото для '
                        'рассылки) -> отправляет рекламу в указанное время\n'
                        '/my_adv -> выводит список рекламных рассылок, которые вы добавили\n'
                        '/delete(параметр: all - если вы хотите удалить все рекламные рассылки, id рекламной '
                        'рассылки, можно получить в функции my_adv) -> удаляет рассылку\n'
                        '/tg(username тг канала) -> обновляет тг канала в общую базу данных\n'
                        '/del_tg(username тг канала) -> удаляет тг канал из общей базы\n'
                        '/my_tg -> выводит все тг каналы в базе данных\n'
                        '/reset -> отчищает промежуточную информацию о рекламной рассылке')
        bot.send_message(message.chat.id, message_text)
        logger.info(f"использована функция пользователем c id {message.chat.id}")


    @bot.message_handler(commands=["stop"])
    @ignoring_not_admin_message
    @logger.catch
    def stop_bot(message) -> None:
        global flag_stop
        for el in ADMIN_CHAT_ID:
            bot.send_message(el, 'Работа бота завершена')
        flag_stop = True
        bot.stop_bot()
        logger.info(f"использована функция пользователем c id {message.chat.id}")
        exit(0)


    @bot.message_handler(commands=["my_adv"])
    @ignoring_not_admin_message
    @logger.catch
    def get_adv_inf(message):
        all_inf = AdvTable.select_adv()
        if not len(all_inf):
            bot.send_message(message.chat.id, "У вас нет рекламы")
            return

        for el in all_inf:
            adv_text_inf, adv_photo_inf, adv_video_inf = el[1].split("&")
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
                    f"<b>каналы куда пойдет рассылка</b>: \n{' '.join(el[3].split('/'))}\n")
            bot.send_message(message.chat.id, text, parse_mode='html')
            logger.info(f"использована функция пользователем c id {message.chat.id}")


    @bot.message_handler(commands=["my_id"])
    def my_id(message) -> None:
        bot.send_message(message.chat.id, f'Ваш id: `{str(message.chat.id)}`', parse_mode='Markdown')


    @bot.message_handler(commands=["delete"])
    @ignoring_not_admin_message
    @logger.catch
    def reset_all_data(message):
        if len(message.text) == 7:
            bot.send_message(message.chat.id, "использована функция без указаний")
            logger.info(f"функция delete без аргументов пользователем c id {message.chat.id}")
            return

        match message.text[7:].lower().strip():
            case "all":
                AdvTable.all_delete_adv()
                logger.info("использована функция delete с аргументом all")
                bot.send_message(message.chat.id, "реклама отчищена")
                return
            case _:
                argument = message.text[7:].lower().strip()
                if argument.isdigit():
                    id_col = [[el[0]] for el in AdvTable.select_adv()]
                    if int(argument) in [el[0] for el in id_col]:
                        AdvTable.delete_adv(int(argument))
                        bot.send_message(message.chat.id, "реклама успешно удалена")
                        logger.info("реклама удалена в функции delete")
                    else:
                        bot.send_message(message.chat.id, "реклама с таким id не найдена")
                        logger.info("реклама не найдена в функции delete")


    @bot.message_handler(commands=["reset"])
    @logger.catch
    def reset_adv_inf(message, local_use=True) -> None:
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
        if local_use:
            bot.send_message(message.chat.id, "вся информация про рекламу отчищена")
        logger.info(f"использована функция пользователем c id {message.chat.id}")


    @bot.message_handler(commands=["tg"])
    @ignoring_not_admin_message
    @logger.catch
    def update_tg(message):
        tg = message.text[3:].strip() if len(message.text) > 3 else ""

        if 'https://t.me' in tg:
            tg = tg.split('/')[-1]

        if '@' in tg:
            tg = tg.replace('@', '')

        checker = Checker(bot)
        if not checker.check_exist_groups(tg=tg, vk="-"):
            bot.send_message(message.chat.id, "ТГ канала не существует")
            logger.info("ТГ канала не существует")
            return

        all_inf = TgChannelTable.select_channel()
        for el in all_inf:
            if el[1] == tg:
                bot.send_message(message.chat.id, "канал уже присутствует в бд")
                logger.info("канал уже присутствует в бд")
                return

        TgChannelTable.insert_channel(tg_channel=tg)
        bot.send_message(message.chat.id, "Канал добавлен ко всем в список")
        logger.info(f"использована функция пользователем c id {message.chat.id}")


    @bot.message_handler(commands=["my_tg"])
    @ignoring_not_admin_message
    @logger.catch
    def getter_my_tg(message):
        tg_list = [[el[1]] for el in TgChannelTable.select_channel()]
        message_text = "Ваши каналы:\n"

        for tg in tg_list:
            message_text += f"`{tg[0]}`\n"

        if message_text.strip() == "Ваши каналы:":
            bot.send_message(message.chat.id, "вы не добавили ни одного канала")
            logger.info(f"использована функция пользователем c id {message.chat.id}")
            return

        logger.info(f"использована функция пользователем c id {message.chat.id}")
        bot.send_message(message.chat.id, message_text, parse_mode="MarkdownV2")


    @bot.message_handler(commands=["del_tg"])
    @ignoring_not_admin_message
    @logger.catch
    def delete_tg_channel(message):
        tg = message.text[7:].strip() if len(message.text) > 7 else ""

        answer = TgChannelTable.delete_channel(tg=tg)
        if answer != "success":
            logger.info(answer)
            bot.send_message(message.chat.id, "что то пошло не так при удалении из бд")
        logger.info(f"использована функция пользователем c id {message.chat.id}")
        bot.send_message(message.chat.id, "канал удален")


    @logger.catch
    def change_submit(call) -> None:
        global my_keyboard, my_group_for_keyboard

        call_data = call.data.split()
        tg, action = call_data[0], call_data[1]
        new_marcup = InlineKeyboardMarkup(row_width=1)
        for i, el in enumerate(my_group_for_keyboard):
            if el == tg:
                if action == "add":
                    status_buttons[el] = "not"
                    my_keyboard[i] = InlineKeyboardButton(text=f"✅{tg}", callback_data=f"{tg} not")
                if action == "not":
                    status_buttons[el] = "add"
                    my_keyboard[i] = InlineKeyboardButton(text=f"{tg}", callback_data=f"{tg} add")

        new_marcup.add(*my_keyboard)
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=new_marcup
        )
        logger.info(f"использована функция пользователем c id {call.message.chat.id}")


    def delete_submit_message(message, check_exist_media=False):
        bot.delete_message(message.chat.id, message.id)
        bot.delete_message(message.chat.id, message.id - 1)
        if check_exist_media:
            bot.delete_message(message.chat.id, message.id - 2)


    @logger.catch
    def save_submit(call):
        global my_keyboard, my_group_for_keyboard, inf_adv, photo_adv, video_adv, text_adv, status_buttons, date_adv

        inf_adv = (f"{text_adv if text_adv else '-'}"
                   f"&{' '.join([el for el in photo_adv]) if photo_adv else '-'}&"
                   f"{' '.join(el for el in video_adv) if video_adv else '-'}")
        check_exist_media = True if photo_adv or video_adv else False
        photo_adv = set()
        video_adv = set()
        list_group = ""
        for tg in my_group_for_keyboard:
            if status_buttons[tg] == "not":
                list_group += f"{tg}/"

        if not list_group:
            reset_adv_inf(call.message, local_use=False)
            delete_submit_message(call.message, check_exist_media=check_exist_media)
            bot.send_message(call.message.chat.id,
                             "вы не выбрали ни одного канала, информация о вашей рекламе отчищена")
            logger.info("не выбрано ни одного паблика в функции save_submit")
            return

        AdvTable.insert_adv(inf_adv=inf_adv, date_post=date_adv, tg_vk_posting=list_group)
        delete_submit_message(call.message, check_exist_media=check_exist_media)
        bot.send_message(call.message.chat.id, "реклама сохранена")
        logger.info(f"использована функция пользователем c id {call.message.chat.id}")
        return


    def del_adv() -> list:
        all_adv = AdvTable.select_adv()
        ready_adv = []
        for el in all_adv:
            if time_difference(el[2]) == -1:
                ready_adv.append(el)
                AdvTable.delete_adv(el[0])
        return ready_adv


    @logger.catch
    def send_adv_posts(adv_lst: list) -> None:
        for adv in adv_lst:
            adv_text_inf, adv_photo_inf, adv_video_inf = adv[1].split("&")
            group_post_adv = [tg for tg in adv[3].split("/") if tg != '']
            for tg in group_post_adv:
                send_adv_message_submit(
                    chat_id=f"@{tg}",
                    video=adv_video_inf,
                    photo=adv_photo_inf,
                    text=adv_text_inf,
                    local_func=True
                )
            logger.info("использована функция")


    @bot.callback_query_handler(func=lambda call: True)
    @logger.catch
    def callback(call):
        match call.data.split()[-1]:
            case "add":
                change_submit(call)
            case "not":
                change_submit(call)
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
            logger.info("Неверный формат времени")
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
                    bot.send_message(chat_id=chat_id, text=text_loc, parse_mode='html')
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
                        bot.send_photo(chat_id=chat_id, photo=list_photo[0], caption=text_loc, parse_mode='html')
                    if len(video_loc) == 1 and len(photo_loc) == 0:
                        list_video = [el for el in video_loc]
                        bot.send_video(chat_id=chat_id, video=list_video[0], caption=text_loc, parse_mode='html')

        except Exception as ex:
            logger.error(f"ошибка в функции send_adv_message: {ex}")


    @bot.message_handler(content_types=["text"])
    @ignoring_not_admin_message
    def adv_newsletter(message) -> None:
        global my_keyboard, my_group_for_keyboard, status_buttons, text_adv, date_adv, message_id_adv, \
            photo_adv, video_adv

        date_adv_text = inf_post_adv(message)
        if not date_adv_text:
            bot.send_message(message.chat.id, "вы ввели что-то не так")
            logger.info("введен неизвестный текст в функции adv_newsletter")
            return

        date = time_difference(date_adv_text[0])
        date_adv = date_adv_text[0]
        if not type(date) is dict:
            reset_adv_inf(message, local_use=False)
            text = ""
            if type(date) is int:
                text = "вы ввели дату, которая меньше нынешней"
            if type(date) is str:
                text = date
            bot.send_message(message.chat.id, text)
            return

        try:
            markup = InlineKeyboardMarkup(row_width=1)
            my_keyboard = []
            my_group_for_keyboard = []
            status_buttons = {}
            text_adv = AdvFormat.formation(date_adv_text[1])
            tg_db_channel = [[el[1]] for el in TgChannelTable.select_channel()]
            tg_channel = set([
                el[0] for el in tg_db_channel
            ])

            for tg in tg_channel:
                status_buttons[tg] = "add"
                my_group_for_keyboard.append(tg)
                my_keyboard.append(InlineKeyboardButton(f"{tg}", callback_data=f"{tg} add"))

            my_keyboard.append(InlineKeyboardButton("подтвердить", callback_data="end"))
            markup.add(*my_keyboard)
            bot.send_message(message.chat.id, "вот ваше сообщение:")
            send_adv_message_submit(message.chat.id)
            message_text = "Выберите каналы, в которые должна пойти рассылка"
            bot.send_message(message.chat.id, message_text, reply_markup=markup)

            logger.info(f"использована функция пользователем c id {message.chat.id}")

        except Exception as ex:
            logger.error(f"{ex} (error)!")
            bot.send_message(message.chat.id, f'Произошла ошибка: {ex} в функции adv_newsletter')


except:
    logger.error(f"{format_exc()}")

print('bot worked')
bot.infinity_polling(timeout=10, long_polling_timeout=150)
logger.info("бот остановлен")
