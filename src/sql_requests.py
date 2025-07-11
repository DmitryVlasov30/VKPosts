from sqlite3 import connect
from pathlib import Path
from json import load

with open("../data.json") as data:
    inf = load(data)
    path = Path(inf["path_to_db"])
    name_tbl = inf["name_table"]
    name_tbl_adv = inf["name_table_adv"]
    name_tbl_channel = inf["all_tg"]


def create_main_table(name_db=name_tbl):
    global path
    db = connect(path)
    curr = db.cursor()
    curr.execute(f"""
        CREATE TABLE IF NOT EXISTS {name_db} (
            "id"	INTEGER NOT NULL UNIQUE,
            "vk_id"	INTEGER NOT NULL,
            "vk_screen"	TEXT NOT NULL,
            "tg_channel"	TEXT NOT NULL,
            "posts_id"	TEXT NOT NULL,
            "quantity"	INTEGER NOT NULL,
            PRIMARY KEY("id" AUTOINCREMENT)
        );
        """)
    db.commit()
    db.close()


def clear_inf(count_posts: int, name_table=name_tbl) -> list:
    global path
    db = connect(path)
    curr = db.cursor()
    try:
        curr.execute(f"""
            SELECT vk_id, tg_channel, posts_id, quantity
            FROM {name_table}
            WHERE quantity > {count_posts}
        """)
        posts = curr.fetchall()
        for element in map(lambda x: list(x), posts):
            arr = element[2].split()
            if len(arr) >= count_posts+10:
                arr = list(sorted(arr, key=lambda x: int(x)))
                arr = arr[-count_posts:]
            else:
                continue

            count = len(arr)
            element[2] = " ".join(arr)
            element[3] = count
            curr.execute(f"""
                UPDATE {name_tbl} SET posts_id = ?, quantity = ?
                WHERE (vk_id = ?) AND (tg_channel = ?)
            """, (element[2], element[3], str(element[0]), str(element[1])))
        return posts
    except Exception as ex:
        print(ex)
    finally:
        db.commit()
        db.close()




def new_inf(vk_id: int, vk_screen: str, tg_channel: str, posts="", name_table=name_tbl):
    global path
    db = connect(path)
    quantity = len(posts.split())
    try:
        curr = db.cursor()
        curr.execute(f"""
                INSERT INTO {name_table} (vk_id, vk_screen, tg_channel, posts_id, quantity) VALUES
                    (?, ?, ?, ?, ?)
            """, (vk_id, vk_screen, tg_channel, posts, quantity))
    except Exception as ex:
        return ex
    finally:
        db.commit()
        db.close()


def delete_inf(vk_id: int, tg_channel: str, name_table=name_tbl):
    global path
    db = connect(path)
    text_mistake = ""
    try:
        curr = db.cursor()
        curr.execute(f"""
            DELETE FROM {name_table}
            WHERE (tg_channel = ?) AND (vk_id = ?)
        """, (tg_channel, vk_id))
    except Exception as ex:
        text_mistake = ex
    finally:
        db.commit()
        db.close()
    return text_mistake



#id, vk_id, vk_screen, tg_channel, posts_id, quantity
def get_db_inf(name_col="*", rule=" ", name_table=name_tbl):
    global path
    db = connect(path)
    all_ready_inf = False
    if name_col != "*":
        name_col.split()
        name_col = ", ".join(name_col.split())

    try:
        curr = db.cursor()
        curr.execute(f"""
            SELECT {name_col}
            FROM {name_table}
            {rule}
        """)
        all_ready_inf = curr.fetchall()
    finally:
        db.commit()
        db.close()
    if all_ready_inf is False:
        return False

    return list(map(lambda el: list(el), all_ready_inf))


def update_inf(vk_id: int, tg_channel: str, posts: str, name_table=name_tbl):
    global path

    flag = True
    db = connect(path)
    curr = db.cursor()
    quantity = len(posts.split())
    try:
        curr.execute(f"""
            UPDATE {name_table} SET posts_id = ?, quantity = ?
            WHERE (vk_id = ?) AND (tg_channel = ?)
        """, (posts, quantity, vk_id, tg_channel))
    except Exception as ex:
        print(ex)
        flag = False
    finally:
        db.commit()
        db.close()
    return flag


def create_adv_table(name_table_adv=name_tbl_adv):
    global path

    db = connect(path)
    curr = db.cursor()
    curr.execute(f"""
        CREATE TABLE IF NOT EXISTS {name_table_adv} (
            "id"	INTEGER NOT NULL UNIQUE,
            "inf_adv"	TEXT NOT NULL,
            "date_post"	TEXT NOT NULL,
            "tg_vk_posting"	TEXT NOT NULL,
            PRIMARY KEY("id" AUTOINCREMENT)
        )
    """)
    db.commit()
    db.close()


def new_adv_inf(inf_adv: str, date_post: str, tg_vk_posting: str, name_table=name_tbl_adv):
    global path

    db = connect(path)
    try:
        curr = db.cursor()
        curr.execute(f"""
                 INSERT INTO {name_table} (inf_adv, date_post, tg_vk_posting) VALUES
                     (?, ?, ?)
             """, (inf_adv, date_post, tg_vk_posting))
    except Exception as ex:
        return ex
    finally:
        db.commit()
        db.close()


def delete_adv_inf(id_del: int, name_table=name_tbl_adv):
    global path

    db = connect(path)
    text_mistake = ""
    try:
        curr = db.cursor()
        curr.execute(f"""
            DELETE FROM {name_table} 
            WHERE (id = ?)     
        """, (id_del,))
    except Exception as ex:
        text_mistake = ex
    finally:
        db.commit()
        db.close()
    return text_mistake


def delete_all_inf(rule="", name_table=name_tbl_adv):
    global path

    db = connect(path)
    text_mistake = ""
    try:
        curr = db.cursor()
        curr.execute(f"""DELETE FROM {name_table} {rule}""")
    except Exception as ex:
        text_mistake = ex
    finally:
        db.commit()
        db.close()
    return text_mistake


def create_tg_table(name_table=name_tbl_channel):
    global path

    db = connect(path)
    curr = db.cursor()
    curr.execute(f"""
        CREATE TABLE IF NOT EXISTS {name_table} (
            "id"	INTEGER NOT NULL UNIQUE,
            "tg_channel"    TEXT NOT NULL,
            PRIMARY KEY("id" AUTOINCREMENT)
        )
    """)
    db.commit()
    db.close()


def new_channel(tg_channel: str, name_table=name_tbl_channel):
    global path

    db = connect(path)
    curr = db.cursor()
    try:
        curr.execute(f"""
            INSERT INTO {name_table} (tg_channel) VALUES
                (?)
        """, (tg_channel,))
    except Exception as ex:
        return ex
    finally:
        db.commit()
        db.close()


def delete_channel(tg):
    global path

    db = connect(path)
    curr = db.cursor()
    try:
        curr.execute(f"""
            DELETE FROM {name_tbl_channel} WHERE tg_channel = ?
        """, (tg,))
    except Exception as ex:
        return ex
    finally:
        db.commit()
        db.close()