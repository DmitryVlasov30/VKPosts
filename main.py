from sql_requests import get_db_inf, new_inf, clear_inf, delete_inf, create_main_table, update_inf, create_adv_table, \
    delete_adv_inf, new_adv_inf, delete_all_inf, name_tbl_adv

import vk_api.exceptions
from vk_api import VkApi
from telebot import TeleBot
from telebot.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaVideo
from json import load
from traceback import format_exc
from datetime import datetime
from threading import Timer

with open("data.json") as data:
    inf = load(data)
    ACCESS_TOKEN_VK = inf["access_token_vk"]
    TOKEN = inf["token"]
    GENERAL_ADMIN = inf["general_admin"]

bot = TeleBot(token=TOKEN)
admin_chat_id = [GENERAL_ADMIN]
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
        inf_text = ""
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


    def filter_photo(vk) -> bool:
        filter_list = []
        if vk in filter_list:
            return True
        return False


    def filter_add(text) -> bool:
        domen_link = []
        for el in domen_link:
            if el in text:
                return False
        if 'http://' in text or 'https://' in text or len(text) == 1 or 't.me/' in text:
            return False
        return True


    def ignoring_not_admin_message(func):
        def wrapper(message):
            global admin_chat_id
            if not str(message.chat.id) in admin_chat_id:
                return
            function = func(message)
            return function

        return wrapper


    @bot.message_handler(commands=["new_adm"])
    @ignoring_not_admin_message
    def new_adm(message) -> None:
        global admin_chat_id
        try:
            admin_id = message.text[8:].strip()
            if admin_id.isdigit():
                if admin_id in admin_chat_id:
                    bot.send_message(message.chat.id, 'Админ уже добавлен')
                    return
                if admin_id.strip() == '':
                    bot.send_message(message.chat.id, 'Неправильные входные данные')
                admin_chat_id.append(str(admin_id))
                bot.send_message(message.chat.id, 'Вы добавили админа')
                bot.send_message(admin_id, 'Вы админ')
            else:
                bot.send_message(message.chat.id,
                                 'В этой функции можно указать только chat id, человек, которого вы хотите добавить может узнать свой chat id командой /my_id')
        except Exception as ex:
            bot.send_message(message.chat.id, f'Произошла ошибка: {ex} в функции new_adm')


    @bot.message_handler(commands=["del_adm"])
    @ignoring_not_admin_message
    def del_adm(message) -> None:
        global admin_chat_id, GENERAL_ADMIN
        try:
            admin = message.text[8:].strip()
            if admin.isdigit():
                if admin in admin_chat_id:
                    index_del_adm = admin_chat_id.index(admin)
                    if admin_chat_id[index_del_adm] == GENERAL_ADMIN:
                        bot.send_message(message.chat.id, 'Нельзя удалить главного админа')
                        return
                    del admin_chat_id[index_del_adm]
                    bot.send_message(message.chat.id, 'Вы удалили админа')
                    bot.send_message(admin, 'Вы теперь не админ')
                else:
                    bot.send_message(message.chat.id, 'Админ не найден')
            else:
                index_admin = -1
                for i, el in enumerate(admin_chat_id):
                    chat = bot.get_chat(el)
                    if chat.username == admin:
                        index_admin = i
                    if el == GENERAL_ADMIN:
                        bot.send_message(message.chat.id, 'Нельзя удалить главного админа')
                        return
                if index_admin != -1:
                    del admin_chat_id[index_admin]
                else:
                    bot.send_message(message.chat.id, 'Админ не найден')
        except Exception as ex:
            bot.send_message(message.chat.id, f'Произошла ошибка: {ex} в функции del_adm')


    @bot.message_handler(commands=["list_adm"])
    @ignoring_not_admin_message
    def adm_list(message) -> None:
        global admin_chat_id
        inf_user = ''
        for el in admin_chat_id:
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
            print(ex)
            pass

        for el in all_message:
            el[1] = sorted(map(int, el[1]))
            posts = " ".join(list(map(str, el[1])))
            update_inf(el[0][0], el[0][1], posts)

        return list(reversed(post_inf))


    @bot.message_handler(commands=["start"])
    def main(message) -> None:
        text_message = ('Вы запустили бота для сборки и пересылки информации из ВКонтакте в Телеграм\n'
                        'Используйте команду /help для вызова списка функций\n\n'
                        '<em><u><i>Сreated by Vlasov</i></u></em>\n'
                        'GitHub -> https://github.com/DmitryVlasov30')
        bot.send_message(message.chat.id, text_message, parse_mode='html')

        start_timer(message)
        create_main_table()
        create_adv_table()


    if not flag_stop:
        def start_timer(message):
            Timer(180, message_post, args=(message,)).start()


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
        except Exception as ex:
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
            bot.send_message(chat, f'Произошла ошибка: {ex} в функции del_group')


    if not flag_stop:
        def message_post(message):
            global admin_chat_id

            try:
                group_inf = get_db_inf(name_col="vk_screen tg_channel vk_id")

                if len(group_inf) == 0:
                    start_timer(message)
                    return

                for vk, tg, id_group_vk in group_inf:

                    new_posts = post_information(id_group_vk, tg)
                    if new_posts is None:
                        for admin in admin_chat_id:
                            bot.send_message(admin, "функция post_information вернула None")
                        return
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
                                pass
                        except Exception as ex:
                            for el in admin_chat_id:
                                bot.send_message(el,
                                    f'Произошла ошибка: {ex} в функции message_post. VK: {vk}, TG: {tg}'
                                )
                            continue


            except Exception as ex:
                for el in admin_chat_id:
                    bot.send_message(el, f'Произошла ошибка: {ex} в функции message_post')
            finally:
                clear_inf(15)
                ready_adv = del_adv()
                send_adv_posts(message, ready_adv)
                start_timer(message)
                return


    @bot.message_handler(commands=["group"])
    @ignoring_not_admin_message
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


    @bot.message_handler(commands=['help'])
    @ignoring_not_admin_message
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


    @bot.message_handler(commands=["my_id"])
    def my_id(message) -> None:
        bot.send_message(message.chat.id, f'Ваш id: `{str(message.chat.id)}`', parse_mode='Markdown')


    @bot.message_handler(commands=["stop"])
    @ignoring_not_admin_message
    def stop_bot(message) -> None:
        global admin_chat_id, flag_stop
        for el in admin_chat_id:
            bot.send_message(el, 'Работа бота завершена')
        flag_stop = True
        bot.stop_bot()
        exit(0)


    @bot.message_handler(commands=["my_adv"])
    @ignoring_not_admin_message
    def get_adv_inf(message):
        all_inf = get_db_inf(name_table=name_tbl_adv)
        if not len(all_inf):
            bot.send_message(message.chat.id, "У вас нет рекламы")
            return

        for el in all_inf:
            print("---", el[1])
            adv_text_inf, adv_photo_inf, adv_video_inf = el[1].split("/")
            send_adv_message_submit(
                message=message,
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


    @bot.message_handler(commands=["reset_all"])
    @ignoring_not_admin_message
    def reset_all_data(message):
        delete_all_inf()
        bot.send_message(message.chat.id, "реклама отчищена")


    @bot.message_handler(commands=["reset_data"])
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


    def add_submit(call) -> None:
        global my_keyboard, my_group_for_keyboard

        call_data = call.data.split()
        vk, tg, action = call_data[0], call_data[1], call_data[2]
        #print(vk, tg)
        new_marcup = InlineKeyboardMarkup(row_width=1)
        #print(my_group_for_keyboard)
        for i, el in enumerate(my_group_for_keyboard):
            # print(el)
            #print(el[-1], tg, "<--tg")
            #print(el[-2], vk, "-_-->vk")
            if el[-2] == tg and el[-1] == vk:
                #print(2)
                status_buttons[f"{el[0]} {el[1]}"] = "not"
                my_keyboard[i] = InlineKeyboardButton(text=f"✅{tg} {vk}", callback_data=f"{tg} {vk} not")
                # print(2)
        new_marcup.add(*my_keyboard)
        #print(new_marcup)
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=new_marcup
        )


    def del_submit(call) -> None:
        global my_keyboard, my_group_for_keyboard

        #print("----")
        call_data = call.data.split()
        vk, tg, action = call_data[0], call_data[1], call_data[2]
        #print(vk, tg)
        new_marcup = InlineKeyboardMarkup(row_width=1)
        #print(my_group_for_keyboard)
        for i, el in enumerate(my_group_for_keyboard):
            # print(el)
            #print(el[-1], tg, "<--tg")
            #print(el[-2], vk, "-_-->vk")
            if el[-1] == tg and el[-2] == vk:
                #print(2)
                status_buttons[f"{el[0]} {el[1]}"] = "add"
                my_keyboard[i] = InlineKeyboardButton(text=f"{tg} {vk}", callback_data=f"{tg} {vk} add")
                # print(2)
        new_marcup.add(*my_keyboard)
        #print(new_marcup)
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=new_marcup
        )


    def save_submit(call):
        global my_keyboard, my_group_for_keyboard, inf_adv, photo_adv, video_adv, text_adv, status_buttons, date_adv

        inf_adv = (f"{text_adv if text_adv else '-'}"
                   f"/{' '.join([el for el in photo_adv]) if photo_adv else '-'}/"
                   f"{' '.join(el for el in video_adv) if video_adv else '-'}")
        photo_adv = set()
        video_adv = set()
        list_group = ""
        for vk, tg in my_group_for_keyboard:
            if status_buttons[f"{vk} {tg}"] == "not":
                list_group += f"{vk} {tg}/"
        new_adv_inf(inf_adv=inf_adv, date_post=date_adv, tg_vk_posting=list_group)
        bot.send_message(call.message.chat.id, "реклама сохраненна")
        return


    def del_adv() -> list:
        all_adv = get_db_inf(name_table=name_tbl_adv)
        ready_adv = []
        for el in all_adv:
            if time_difference(el[2]) == -1:
                ready_adv.append(el)
                delete_adv_inf(el[0])
        return ready_adv


    def send_adv_posts(message, adv_lst: list) -> None:
        list_channel = get_db_inf(name_col="vk_screen tg_screen")
        for adv in adv_lst:
            send_adv_message_submit(
                message,
                chat_id=f"@{adv[3].split()[0]}",
                local_func=True
            )


    @bot.callback_query_handler(func=lambda call: True)
    def callback(call):
        match call.data.split()[-1]:
            case "add":
                add_submit(call)
            case "not":
                del_submit(call)
            case "end":
                save_submit(call)


    def inf_post_adv(message):
        message_text = message.text
        if message_text is None or message_text[:4].strip() != "/adv":
            return
        message_text = message_text[1:]
        idx_start = message_text.find("/") + 1
        idx_end = message_text[idx_start:].find("/") + idx_start
        date = message_text[idx_start:idx_end]
        text_adv_inf = message_text[idx_end + 1:].strip()
        return date, text_adv_inf


    @bot.message_handler(content_types=["video", "photo"])
    def add_video_photo(message) -> None:
        global video_adv, photo_adv, text_adv
        match message.content_type:
            case "video":
                video_adv.add(message.video.file_id)
            case "photo":
                photo_adv.add(message.photo[-1].file_id)


    def time_difference(input_time):
        try:
            given_time = datetime.strptime(input_time, "%H:%M %d.%m.%Y")
        except ValueError:
            return "Неверный формат времени. Используйте 'часы:минуты день.месяц.год'."
        current_time = datetime.now()
        current_time, given_time = given_time, current_time
        if current_time >= given_time:
            difference = current_time - given_time

            print(difference)
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


    def send_adv_message_submit(message, chat_id, photo="-", video="-", text="-", local_func=False):
        global photo_adv, video_adv, text_adv

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
            print(len(photo_loc))
            if len(photo_loc) == 0 and len(video_loc) == 0:
                bot.send_message(chat_id=chat_id, text=text_loc)
            if len(video_loc) != 0 and len(photo_loc) != 0:
                print(8)
                for i, el in enumerate(video_loc):
                    if i == 0:
                        list_video.append(InputMediaVideo(media=el, caption=text_loc))
                        continue
                    list_video.append(InputMediaVideo(media=el))
                list_photo = [InputMediaPhoto(media=el) for el in photo_loc]
            elif len(photo_loc) > 1 and len(video_loc) == 0:
                print(9)
                for i, el in enumerate(photo_loc):
                    if i == 0:
                        list_photo.append(InputMediaPhoto(media=el, caption=text_loc))
                        continue
                    list_photo.append(InputMediaPhoto(media=el))
            elif len(video_loc) > 1 and len(photo_loc) == 0:
                print(10)
                for i, el in enumerate(video_loc):
                    if i == 0:
                        list_video.append(InputMediaVideo(media=el, caption=text_loc))
                        continue
                    list_video.append(InputMediaVideo(media=el))
            print(11)

            if len(video_loc) + len(photo_loc) > 1:
                media_all.extend(list_photo)
                media_all.extend(list_video)
                bot.send_media_group(chat_id=chat_id, media=media_all)
            else:
                print(12)
                if len(photo_loc) == 1 and len(video_loc) == 0:
                    list_photo = [el for el in photo_loc]
                    bot.send_photo(chat_id=chat_id, photo=list_photo[0], caption=text_loc)
                if len(video_loc) == 1 and len(photo_loc) == 0:
                    list_video = [el for el in video_loc]
                    bot.send_video(chat_id=chat_id, video=list_video[0], caption=text_loc)


    @bot.message_handler(content_types=["text"])
    @ignoring_not_admin_message
    def adv_newsletter(message) -> None:
        global my_keyboard, my_group_for_keyboard, status_buttons, text_adv, date_adv, message_id_adv, photo_adv, video_adv
        date_adv_text = inf_post_adv(message)
        if not date_adv_text:
            bot.send_message(message.chat.id, "вы ввели что-то не так")
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

            for tg, vk in vk_public:
                status_buttons[f"{vk} {tg}"] = "add"
                my_group_for_keyboard.append([vk, tg])
                my_keyboard.append(InlineKeyboardButton(f"{tg} {vk}", callback_data=f"{tg} {vk} add"))

            my_keyboard.append(InlineKeyboardButton(f"подтвердить", callback_data="end"))
            markup.add(*my_keyboard)
            bot.send_message(message.chat.id, "вот ваше сообщение:")
            send_adv_message_submit(message, message.chat.id)
            message_text = "Выберите каналы, в которые должна пойти рассылка"
            bot.send_message(message.chat.id, message_text, reply_markup=markup)


        except Exception as ex:
            bot.send_message(message.chat.id, f'Произошла ошибка: {ex} в функции adv_newsletter')


except:
    print(format_exc())

print('bot worked')
bot.infinity_polling(timeout=10, long_polling_timeout=150)