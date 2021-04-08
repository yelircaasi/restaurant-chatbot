import psycopg2
from rasa_sdk.events import SlotSet

SQL_USER = "postgres"
SQL_PASSWORD = "813474"
SQL_HOST = "127.0.0.1" 
SQL_PORT = "5433"
SQL_DATABASE = "postgres"

message_with_name = {
    "calories": lambda name, value: "{0} hat {1} Kalorien.".format(name, value),
    "price": lambda name, value: "{0} kostet {1:.2f}.".format(name, value),
    "rating": lambda name, value: "{0} hat eine Bewertung von {1}.".format(name, value)
    }

message_nameless = {
    "calories": lambda value: "{0} Kalorien".format(value),
    "price": lambda value: "Preis von {0:.2f}".format(value),
    "rating": lambda value: "Bewertung: {0}".format(value)
    }


def fetch_rows(query,
               user=SQL_USER, 
	             password=SQL_PASSWORD, 
	             host=SQL_HOST, 
	             port=SQL_PORT, 
	             database=SQL_DATABASE):
    connection = psycopg2.connect(user=user,
                                  password=password,
                                  host=host, 
                                  port=port, 
                                  database=database)
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    return rows


def get_latest_entities(tracker):
     return [x.get("entity") for x in tracker.latest_message.get("entities", []) if x.get("value") is not None]


def excl_reset(ent1, ent2, val1, val2, entlist):
    bool1 = int(ent1 in entlist)
    bool2 = int(ent2 in entlist)
    onlyone = bool1 + bool2
    if onlyone % 2 == 0:
        return val1, val2
    elif bool1:
        return val1, None
    elif bool2:
        return None, val2

    


def check_restaurant(name_raw=None, attribute=None):
    """
    Queries database for restaurant, based on one or both
      of name and and attribute.
    Returns restaurant names and ids matching the request.
    """        
    if (not name_raw) and (not attribute):
        code = -1
        message = "Was für ein Restaurant suchst du?"
        output = []
        return code, message, output
    elif attribute and name_raw:
        # TODO: fix so that only name in most recent line is taken into consideration
        q = restaurants_by_name_and_attribute(name_raw, attribute)
    elif name_raw:
        q = restaurants_by_name(name_raw)
    elif attribute:
        q = restaurants_by_attribute(attribute)
    options = fetch_rows(q)
    n_rests = len(options)
    if n_rests == 0: 
        message = "Nichts gefunden."
        return 0, message, options, []
    elif n_rests == 1:
        code = 1
        cand = options[0] 
        resto_string = cand[0]
        message = "Hier habe ich etwas für dich gefunden:\n  {0}".format(resto_string)
        resto_id = cand[0]
        resto_name = cand[1]
        output = [SlotSet("restaurant_name", resto_name), SlotSet("resto_id", resto_id)]
    else:
        code = 2
        resto_string = "  " + "\n  ".join([c[0] for c in options])
        message = "Hier habe ich etwas für dich gefunden:\n{0}".format(resto_string)
        icl = dict(enumerate(options))
        output = [SlotSet("restaurant_candidates_list", icl)]
    return code, message, options, output

    





def check_item(name_raw):
    """
    Queries database for item, based on item name.
    Returns item names and ids matching the request.
    """
    if name_raw is None:
        message = "Ich verstehe leider noch nicht, was du suchst."
        return -1, message, [], []
    q = items_by_name(name_raw)
    options = fetch_rows(q)
    n_items = len(options)
    if n_items == 0:
        code = 0
        message = "Nichts gefunden."
        output = []
    elif n_items == 1:
        code = 1
        cand = options[0] 
        item_string = cand[0]
        message = "Hier habe ich etwas für dich gefunden:\n  {0}".format(item_string)
        item_id = cand[0]
        item_name = cand[1]
        output = [SlotSet("item_name", item_name), SlotSet("item_id", item_id)]
    else:
        code = 2
        item_string = "  ".join([c[0] for c in options])
        message = "Hier habe ich etwas für dich gefunden:\n  {0}".format(item_string)
        icl = dict(enumerate(options))
        output = [SlotSet("item_candidates_list", icl)]
    return code, message, options, output


def get_resto_info(info, resto_name_raw=None, resto_id=None, resto_attr=None):
    """
    Generic way to get some restaurant info.
    Used in several actions.
    """
    resto_name = ""
    if (resto_id is None) and (not resto_name_raw) and (not resto_attr):
        message = "Es tut mir Leid, ich weiß immer noch nicht, was für ein Restaurant du willst."
        return message, []
    elif resto_id is None:
        code, message, cands, output = check_restaurant(resto_name_raw, resto_attr)
        if code == -1:
            return message, []
        elif code == 0:
            return message, []
        else:
            resto_id = cands[0][1]
            resto_name = cands[0][0]
    q = info_from_restaurant_id(resto_id, info)
    rows = fetch_rows(q)
    if resto_name:
        message = message_with_name[info](resto_name, rows[0][0])
    else:
        message = message_nameless[info](rows[0][0])
    output = [SlotSet("restaurant_name", resto_name), SlotSet("restaurant_id", resto_id)]
    return message, output


def get_item_info(info, item_name_raw=None, item_id=None):
    """
    Generic way to get some item info.
    Used in several actions.
    """
    item_name = None
    if (item_id is None) and (not item_name_raw):
      message = "Es tut mir Leid, ich weiß immer noch nicht, welchen Menupunkt du meinst."
      return message, []
    if not item_id:
        code, message, cands, output = check_item(item_name_raw)
        if code == -1:
            return message, []
        elif code == 0:
            return message, []
        else:
            item_id = cands[0][1]
            item_name = cands[0][0]
    q = info_from_item_id(item_id, info)
    rows = fetch_rows(q)
    if item_name:
        message = message_with_name[info](item_name, rows[0][0])
    else:
        message = message_nameless[info](rows[0][0])
    output = [SlotSet("item_name", item_name), SlotSet("item_id", item_id)]
    return message, output


restaurants_by_name = lambda name: """
SELECT restaurant_name, id
FROM (SELECT restaurant_name, 
       id, 
       SIMILARITY(restaurant_name, '{0}') AS sim 
FROM restaurants) 
AS temp
WHERE sim>0.3 OR LOWER(restaurant_name) LIKE LOWER('%{0}%')
ORDER BY sim DESC 
LIMIT 3;
""".format(name)


# change name to restaurant_attribute
restaurants_by_attribute = lambda attribute: """
SELECT restaurant_name, id
FROM (SELECT restaurant_name, 
             id, 
             SIMILARITY(cuisine, '{0}') AS sim 
FROM restaurants) 
AS temp
WHERE sim>0.6
ORDER BY sim DESC 
LIMIT 5;
""".format(attribute.lower())


restaurants_by_name_and_attribute = lambda name, attribute: """
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX{}{}
""".format(name, attribute)


items_by_name = lambda name: """
SELECT * 
FROM (SELECT item_name, 
             item_id, 
             SIMILARITY(item_name, '{0}') AS sim 
      FROM items) 
AS temp
WHERE sim>0.3 OR LOWER(item_name) LIKE LOWER('%{0}%')
ORDER BY sim DESC 
LIMIT 5;
""".format(name)


items_by_id = lambda attribute: """
SELECT * 
FROM items
WHERE item_id={0}
""".format(attribute)


items_by_name_and_attribute = lambda name, attribute: """
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX{}{}
""".format(name, attribute)


# change name to restaurant_attribute
recommendation_by_attribute = lambda attribute: """
SELECT restaurant_name, id, rating
FROM (SELECT restaurant_name, 
             id, 
             rating,
             SIMILARITY(cuisine, '{0}') AS sim 
FROM restaurants) 
AS temp
WHERE sim>0.6
ORDER BY rating DESC 
LIMIT 5;
""".format(attribute.lower())


recommendation_wo_attribute = """
SELECT restaurant_name, id, rating
FROM restaurants
ORDER BY rating DESC 
LIMIT 5;
"""


get_item = lambda item_id: """
SELECT item_name, item_id 
FROM items
WHERE item_id={0}
""".format(item_id)


info_from_item_id = lambda item_id, info: """
SELECT {1} 
FROM items
WHERE item_id={0}
""".format(item_id, info)


info_from_restaurant_id = lambda item, info: """
SELECT {1} 
FROM restaurants
WHERE id={0}
""".format(item, info)


menu_from_restaurant_id = lambda restaurant_id: """
SELECT item_name, price, item_id, id, restaurant_name  
FROM restaurants INNER JOIN items
ON id=restaurant_id
WHERE restaurant_id={0};
""".format(restaurant_id)


