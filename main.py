import vk_api.exceptions
from vk_api import VkApi
from telebot import TeleBot
from telebot.types import InputMediaPhoto

from threading import Timer


ACCESS_TOKEN_VK = 'YOUR VK TOKEN'
TOKEN = 'YOUR TOKEN BOT'
bot = TeleBot(token=TOKEN)
general_admin = 'YOUR TG ID'
admin_chat_id = [general_admin]
flag_stop = False




try:

    def check_exist_groups(vk, tg):
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
        if flag_tg and flag_vk:
            return True

        return False



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


    def clear_func(arr):
        try:
            for el in arr:
                if len(el[1]) >= 15:
                    el[1] = list(sorted(map(int, el[1])))
                    el[1] = el[1][-10:]
            inf = ''
            for el in arr:
                message_string = ''
                for mess_id in el[1]:
                    message_string += str(mess_id) + '/'
                inf += f'{"{" + el[0][0] + "." + el[0][1] + "." + el[0][2] + "}"}{message_string}'
                if inf == '':
                    return
                with open('message_id.txt', 'w') as file:
                    file.write(inf.replace(' ', ''))
                    file.close()
        except Exception as ex:
            print(ex)


    def get_inf_message():
        with open('message_id.txt', 'r') as file:
            text = file.read()
            file.close()

        text = text.split('{')
        for el in text:
            if not el:
                del text[text.index(el)]

        arr = [[el.split('}')[0].split('.'), el.split('}')[1].split('/')] for el in text]

        for el in arr:
            if '' in el[1]:
                del el[1][el[1].index('')]

        return arr


    def add_inf_message(vk, tg):
        id_group = group_all_information(vk, 'id')
        if id_group is None:
            return False
        with open('message_id.txt', 'a') as file:
            file.seek(0, 2)
            file.write(f"{'{' + vk + '.' + tg + '.' + id_group + '}'}")
            file.close()


    def del_message_id(vk, tg):
        message_list = get_inf_message()
        index = -1
        flag_last_el = False
        if len(message_list) == 1:
            flag_last_el = True
        for i, el in enumerate(message_list):
            if el[0][0] == vk and el[0][1] == tg:
                index = i

        if index == -1:
            return 'Не удалось удалить группу'

        del message_list[index]

        inf = ''
        for el in message_list:
            message_string = ''
            for mess_id in el[1]:
                message_string += mess_id + '/'
            inf += f'{"{" + el[0][0] + "." + el[0][1] + "." + el[0][2] + "}"}{message_string}'
        if inf == '' and not flag_last_el:
            return
        with open('message_id.txt', 'w') as file:
            file.write(inf)
            file.close()



    def filter_photo(vk):
        filter_list = ['maimoscow']
        if vk in filter_list:
            return True
        return False


    def filter_add(text):
        domen_link = ['.com', '.net', '.ru', '.рф', 'Ребята, сохраняйте контакты, помогут в учебе😉', 'club', 'Создали общую беседу для Вас (для всех курсов), там вы сможете знакомиться, задавать вопросы, искать задания и т.д.', 'впостер', '@tech_univers']
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
    def new_adm(message):
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
                bot.send_message(message.chat.id, 'В этой функции можно указать только chat id, человек, которого вы хотите добавить может узнать свой chat id командой /my_id')
        except Exception as ex:
            bot.send_message(message.chat.id, f'Произошла ошибка: {ex} в функции new_adm')


    @bot.message_handler(commands=["del_adm"])
    @ignoring_not_admin_message
    def del_adm(message):
        global admin_chat_id, general_admin
        try:
            admin = message.text[8:].strip()
            if admin.isdigit():
                if admin in admin_chat_id:
                    index_del_adm = admin_chat_id.index(admin)
                    if admin_chat_id[index_del_adm] == general_admin:
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
                    if el == general_admin:
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
    def adm_list(message):
        global admin_chat_id
        inf = ''
        for el in admin_chat_id:
            chat = bot.get_chat(int(el))
            username = chat.username
            inf += f'id: `{el}`, username: `@{username}`\n'
        bot.send_message(message.chat.id, inf, parse_mode='Markdown')


    def post_information(groups_name, group_tg):
        global ACCESS_TOKEN_VK
        vk = VkApi(token=ACCESS_TOKEN_VK)
        post_inf = []
        all_message = get_inf_message()
        all_inf = get_inf_message()
        group_id = 0
        group_inf = [[group[0], group[1], group[2]] for group, message in all_inf]
        for vk_group, tg, vk_id in group_inf:
            if vk_group == groups_name and tg == group_tg:
                group_id = int(vk_id)
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
                    if el[0][0] == groups_name and el[0][1] == group_tg:
                        id_post = el[1]
                if not str(post.get('id', '')) in list(map(str, id_post)):
                    for el in all_message:
                        if el[0][0] == groups_name and el[0][1] == group_tg:
                            el[1].append(str(post.get('id')))
                    text_post = post.get('text', '')
                    list_size_photo = []
                    if 'attachments' in post:
                       for attachments in post['attachments']:
                            if attachments['type'] == 'photo':
                                for count, link in enumerate(attachments['photo']['sizes']):
                                    if count == len(attachments['photo']['sizes'])-1:
                                        list_size_photo.append(link['url'])
                    post_inf.append([text_post, list_size_photo])

        except vk_api.exceptions.ApiError as ex:
            print(ex)
            pass

        inf = ''

        for el in all_message:
            message_string = ''
            el[1] = sorted(map(int, el[1]))
            for mess_id in map(str, el[1]):
                message_string += mess_id + '/'
            inf += f'{"{" + el[0][0] + "." + el[0][1] + "." + el[0][2] + "}"}{message_string}'
        if inf == '':
            return
        with open('message_id.txt', 'w') as file:
            file.write(inf)
            file.close()

        return list(reversed(post_inf))


    @bot.message_handler(commands=["start"])
    def start(message):
        text_message = ('Вы запустили бота для сборки и пересылки информации из ВКонтакте в Телеграм\n'
                        'Используйте команду /help для вызова списка функций\n\n'
                        '<em><u><i>Сreated by Vlasov</i></u></em>\n'
                        'GitHub -> https://github.com/DmitryVlasov30')
        bot.send_message(message.chat.id, text_message, parse_mode='html')

        start_timer(message)

    if not flag_stop:
        def start_timer(message):
            Timer(180, message_post, args=(message,)).start()



    @bot.message_handler(commands=["add"])
    @ignoring_not_admin_message
    def add_vk_tg_group(message):
        chat = message.chat.id
        try:
            all_inf = get_inf_message()
            vk, tg = message.text[4:].strip().split()

            if 'https://vk.com' in vk:
                vk = vk.split('/')[-1]

            if 'https://t.me' in tg:
                tg = tg.split('/')[-1]

            if '@' in tg:
                tg = tg.replace('@', '')

            if not check_exist_groups(vk, tg):
                bot.send_message(chat, 'Группы вк или тг не существует')
                return

            vk = group_all_information(vk, 'screen_name')

            flag_exists = False
            for group, message in all_inf:
                if group[0] == vk and group[1] == tg:
                    flag_exists = True
            if flag_exists:
                bot.send_message(chat, 'Группа уже отслеживается')
                return

            add_inf_message(vk, tg)
            bot.send_message(chat, 'Группa отслеживается')
        except Exception as ex:
            bot.send_message(chat, f'Произошла ошибка: {ex} в функции add_vk_tg_group')


    @bot.message_handler(commands=['del'])
    @ignoring_not_admin_message
    def del_group(message):
        chat = message.chat.id
        try:
            all_inf = get_inf_message()

            vk, tg = message.text[4:].strip().split()

            if 'https://vk.com' in vk:
                vk = vk.split('/')[-1]

            if 'https://t.me' in tg:
                tg = tg.split('/')[-1]

            if '@' in tg:
                tg = tg.replace('@', '')

            flag_exists = False
            for group, message in all_inf:
                if group[0] == vk and group[1] == tg:
                    flag_exists = True
            if not flag_exists:
                bot.send_message(chat, 'Группа не найдена')
                return

            text_otv = del_message_id(vk, tg)
            if not text_otv is None:
                bot.send_message(chat, text_otv)
                return
            bot.send_message(chat, 'Группа удалена')
        except Exception as ex:
            bot.send_message(chat, f'Произошла ошибка: {ex} в функции del_group')


    if not flag_stop:
        def message_post(message):
            global admin_chat_id

            try:
                all_inf = get_inf_message()

                if len(all_inf) == 0:
                    start_timer(message)
                    return
                group_inf = [[group[0], group[1], group[2]] for group, message in all_inf]
                for vk, tg, id_group_vk in group_inf:

                    new_posts = post_information(vk, tg)
                    if new_posts is None:
                        for admin in admin_chat_id:
                            bot.send_message(admin, "данные потеряны :(")
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
                                 bot.send_message(el, f'Произошла ошибка: {ex} в функции message_post. VK: {vk}, TG: {tg}')
                            continue


            except Exception as ex:
                for el in admin_chat_id:
                    bot.send_message(el, f'Произошла ошибка: {ex} в функции message_post')
            finally:
                clear_func(get_inf_message())
                start_timer(message)
                return



    @bot.message_handler(commands=["group"])
    @ignoring_not_admin_message
    def get_group_list(message):
        all_inf = get_inf_message()
        group_inf = [[group[0], group[1], group[2]] for group, message in all_inf]
        for el in group_inf:
            if not el:
                del group_inf[group_inf.index(el)]

        if len(group_inf) == 0:
            bot.send_message(message.chat.id, "У вас нет групп")
            return

        inf = 'Ваши группы:\n'
        for vk, tg, id_vk in group_inf:
            vk_name = group_all_information(id_vk, 'screen_name')
            vk_link = f'https://vk.com/{vk_name}'
            inf += (f'*VK*: `{vk_name}`\n'
                    f'*TG*: `{tg}`\n'
                    f'*[LINK]({vk_link})*\n\n')
        bot.send_message(message.chat.id, inf, parse_mode='MarkdownV2', disable_web_page_preview=True)


    @bot.message_handler(commands=['help'])
    @ignoring_not_admin_message
    def help_func(message):
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
    def my_id(message):
        bot.send_message(message.chat.id, f'Ваш id: `{str(message.chat.id)}`', parse_mode='Markdown')


    @bot.message_handler(commands=["stop"])
    @ignoring_not_admin_message
    def stop_bot(message):
        global admin_chat_id, flag_stop
        for el in admin_chat_id:
            bot.send_message(el, 'Работа бота завершена')
        flag_stop = True
        bot.stop_bot()

except Exception as all_mistake:
    print(all_mistake)


print('bot worked')
bot.infinity_polling(timeout=10, long_polling_timeout=150)