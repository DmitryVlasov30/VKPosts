from loguru import logger
from src.config import settings


class AdvFormat:

    @staticmethod
    def format_link(text: str, link: str) -> str:
        return f'<a href="{link}">{text}</a>'

    @staticmethod
    @logger.catch
    def formation(message_text: str):
        start_link = -1
        end_link = -1
        ans = []
        link_list = []
        for i in range(len(message_text)):
            if message_text[i] == "[":
                start_link = i
            if message_text[i] == "]":
                end_link = i
            if start_link != -1 and end_link != -1:
                text_to_link = message_text[start_link+1: end_link]
                link_list.append(f"[{text_to_link}]")
                if len(text_to_link.split("|")) == 2:
                    text, link = text_to_link.split("|")
                    text, link = text.strip(), link.strip()
                    if "http" in link or "https" in link:
                        ans.append([AdvFormat.format_link(
                            text=text,
                            link=link
                        ), end_link])
                start_link, end_link = -1, -1

        border = 0
        for link, idx in ans:
            message_text = message_text[:idx + border + 1] + link + message_text[idx + border + 1:]
            border += len(link)

        for el in link_list:
            message_text = message_text.replace(el, "")

        return message_text


class FilterAdv:

    @staticmethod
    def filter_photo(vk) -> bool:
        filter_list = settings.photo_skip

        if vk in filter_list:
            return True
        return False

    @staticmethod
    def filter_add(text) -> bool:
        domain_link = settings.blacklist
        link = settings.skip_link
        for el in domain_link:
            if el in text:
                return False
        if not link:
            return True
        if 'http://' in text or 'https://' in text or len(text) == 1 or 't.me/' in text:
            return False
        return True

    @staticmethod
    def replace_warning_word(text_post: str, tg: str):
        replace_word = settings.replace_word
        for word in replace_word:
            text_post = text_post.replace(word, "")
        return text_post
