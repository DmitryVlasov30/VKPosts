from json import load


def filter_photo(vk) -> bool:
    with open("data.json") as file:
        filter_list = load(file)["photo_skip"]

    if vk in filter_list:
        return True
    return False


def filter_add(text) -> bool:
    with open("data.json") as file:
        domain_link = load(file)["blacklist"]

    for el in domain_link:
        if el in text:
            return False
    if 'http://' in text or 'https://' in text or len(text) == 1 or 't.me/' in text:
        return False
    return True