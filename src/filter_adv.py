from json import load


with open("../data.json") as f:
    data = load(f)
    skip_link = data["skip_link"]


def filter_photo(vk) -> bool:
    with open("../data.json") as file:
        filter_list = load(file)["photo_skip"]

    if vk in filter_list:
        return True
    return False


def filter_add(text) -> bool:
    with open("../data.json") as file:
        domain_link = load(file)["blacklist"]

    for el in domain_link:
        if el in text:
            return False
    if not skip_link:
        return True
    if 'http://' in text or 'https://' in text or len(text) == 1 or 't.me/' in text:
        return False
    return True


def replace_warning_word(text_post: str, tg: str):
    with open("../data.json") as file:
        replace_word = load(file)["replace_word"]

    for word in replace_word:
        text_post = text_post.replace(word, "")
    return text_post