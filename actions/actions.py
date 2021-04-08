#import json
from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import actions.query_utils as qu
#import psycopg2


#SQL_USER = "postgres"
#SQL_PASSWORD = "813474"
#SQL_HOST = "127.0.0.1" 
#SQL_PORT = "5433"
#SQL_DATABASE = "postgres"


class ActionClarify(Action): # good
    def name(self):
        return "action_clarify"

    async def run(self, dispatcher, tracker, domain):
        counter = tracker.get_slot("out_of_scope_counter")
        if counter is None:
            counter = 0
        if counter == 0:
            dispatcher.utter_message(text="Es tut mir Leid, ich habe nicht verstanden. Kannst du das bitte anders formulieren?")
        else: 
            dispatcher.utter_message(text="Ich komme leider nicht mit deiner anfrage zurecht. Ich kann zwar nicht alles, aber ich kann dir helfen, ein Restaurant zu finden und dir das Menü zeigen.")
        counter += 1
        return [SlotSet("out_of_scope_counter", counter)]


class ActionRetrieveRestaurant(Action): #TODO: check
    """

    """    

    def name(self):
        return "action_retrieve_restaurant"

    async def run(self, dispatcher, tracker, domain):
        resto_raw = tracker.get_slot("restaurant_name_raw")
        resto_attr = tracker.get_slot("restaurant_attribute")

        latest = qu.get_latest_entities(tracker)
        resto_raw, resto_attr = qu.excl_reset("restaurant_name_raw", "restaurant_attribute", 
                                              resto_raw, resto_attr, latest)
        code, message, options, output = qu.check_restaurant(resto_raw, resto_attr)
        dispatcher.utter_message(text=message)
        return output

'''
class ActionSelectRestaurant(Action): #TODO: check
    """

    """    

    def name(self):
        return "action_select_restaurant"

    async def run(self, dispatcher, tracker, domain):
        cands = tracker.get_slot("restaurant_candidates_list")
        n = tracker.get_slot("choice_number")
        try:
            choice = cands[n]
            rest_id = choice[0]
            rest_name = choice[1]
            dispatcher.utter_message(text="{0} gewählt.".format(rest_name))
            return [SlotSet("restaurant_name", rest_name), SlotSet("restaurant_id", rest_id)]
        except:
            dispatcher.utter_message(text="Ich habe etwas nicht verstanden. Welche Option möchtest du wählen?")
            return []


class ActionSelectItem(Action): #TODO: check
    """

    """
    def name(self):
        return "action_select_item"

    async def run(self, dispatcher, tracker, domain):
        cands = tracker.get_slot("item_candidates_list")
        n = tracker.get_slot("choice_number")
        if n is None:
            return []
        try:
            choice = cands[n]
            item_id = choice[0]
            item_name = choice[1]
            dispatcher.utter_message(text="{0} gewählt.".format(item_name))
            return [SlotSet("item_name", item_name), SlotSet("item_id", item_id)]
        except:
            dispatcher.utter_message(text="Ich habe etwas nicht verstanden. Welche Option möchtest du wählen?")
            return []
'''

class ActionGiveRecommendation(Action): #TODO: test
    """

    """
    def name(self):
        return "action_give_recommendation"

    async def run(self, dispatcher, tracker, domain):
        attribute = tracker.get_slot("restaurant_attribute")
        if attribute:
            q = qu.recommendation_by_attribute(attribute)
        else:
            q = qu.recommendation_wo_attribute
        rows = qu.fetch_rows(q) # name, id, rating
        display = "\n  ".join(["{0:<3}{1:<20}{2:>2.1f}".format(str(n)+')', c[0], c[1]) for n,c in enumerate(rows)])
        dispatcher.utter_message(text="Hier sind ein Paar Vorschläge für dich:\n  {0}".format(display))
        return [SlotSet("restaurant_candidates_list", dict(enumerate(rows)))]





class ActionRetrieveMenu(Action): 
    """
    
    """
    def name(self):
        return "action_retrieve_menu"
    
    async def run(self, dispatcher, tracker, domain):

        # fix this to safely use id
        name_raw = tracker.get_slot("restaurant_name_raw")
        if not name_raw:
            dispatcher.utter_message("Ich weiß leider nicht, welches Restaurant du meinst. Frage mich bitte nochmal mit dem Restaurantnamen.")
            return []
        code, message, rows, output = qu.check_restaurant(name_raw)
        if code <= 0:
            dispatcher.utter_message("Ich habe leider nichts gefunden. Frage mich bitte nochmal mit dem genauen Restaurantnamen.")
            return []
        else:
            resto_id = rows[0][1]
            menu_rows = qu.fetch_rows(qu.menu_from_restaurant_id(resto_id))
            menu = "\n  ".join(["{0:<20}{1:>.2f}".format(r[0], r[1]) for r in menu_rows])
            resto_name = menu_rows[0][-1]
            message = "Hier ist das menu von {0}:\n  {1}".format(resto_name, menu)
            dispatcher.utter_message(text=message)
            return []



class ActionRetrieveItem(Action): ###########################################################################################
    """

    """
    def name(self):
        return "action_retrieve_item"

    async def run(self, dispatcher, tracker, domain):
        item_name_raw = tracker.get_slot("item_name_raw")
        

        # fix this with additional check!
        latest = qu.get_latest_entities(tracker)
        if "item_name_raw" in latest and ("item_id" not in latest):
            item_id = None
        else:
            item_id = tracker.get_slot("item_id")

        message1, output = qu.get_item_info("calories", item_name_raw, item_id)
        message2, output = qu.get_item_info("price", item_name_raw, item_id)
        dispatcher.utter_message(text="\n".join([message1, message2]))
        return output

class ActionRetrieveCalories(Action): #TODO: test
    """

    """
    def name(self): 
        return "action_retrieve_calories"
        
    async def run(self, dispatcher, tracker, domain):
        item_name_raw = tracker.get_slot("item_name_raw")

        # fix this with additional check!
        latest = qu.get_latest_entities(tracker)
        if "item_name_raw" in latest and ("item_id" not in latest):
            item_id = None
        else:
            item_id = tracker.get_slot("item_id")

        message, output = qu.get_item_info("calories", item_name_raw, item_id)
        dispatcher.utter_message(text=message)
        return output


class ActionRetrievePrice(Action): #TODO: test
    """

    """
    def name(self): 
        return "action_retrieve_price"

    async def run(self, dispatcher, tracker, domain):
        item_name_raw = tracker.get_slot("item_name_raw")
        
        # fix this with additional check!
        latest = qu.get_latest_entities(tracker)
        if "item_name_raw" in latest and ("item_id" not in latest):
            item_id = None
        else:
            item_id = tracker.get_slot("item_id")
        
        message, output = qu.get_item_info("price", item_name_raw, item_id)
        dispatcher.utter_message(text=message)
        return output


class ActionRetrieveRatings(Action): #TODO: test
    """

    """
    def name(self):
        return "action_retrieve_ratings"

    async def run(self, dispatcher, tracker, domain):
        resto_name_raw = tracker.get_slot("restaurant_name_raw")
        
        # fix this with additional check!
        latest = qu.get_latest_entities(tracker)
        if "restaurant_name_raw" in latest and ("restaurant_id" not in latest):
            resto_id = None
        else:
            resto_id = tracker.get_slot("restaurant_id")

        message, output = qu.get_resto_info("rating", resto_name_raw, resto_id)
        dispatcher.utter_message(text=message)
        return output

# LATER: add capability to view items by restaurant and by attribute
