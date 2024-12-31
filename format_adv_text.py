from loguru import logger


def format_link(text: str, link: str) -> str:
    return f'<a href="{link}">{text}</a>'


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
                    ans.append([format_link(
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
