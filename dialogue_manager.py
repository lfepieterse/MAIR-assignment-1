import random

from dialogue_state import(
    GREET,
    COLLECT_PREFERENCES,
    ASK_EXTRA_REQUIREMENTS,
    END,
    RECOMMEND,
    create_dialogue
)
from slot_extraction import ONTOLOGY, extract_slots
from restaurant_repository import find_matching_restaurants


QUESTIONS = {
        "food": "What type of food would you like?",
        "pricerange": "What price range do you prefer: cheap, moderate, or expensive?",
        "area": "Which area would you prefer: north, south, east, west, or centre?"
}


def get_missing_preferences(preferences):
    #preferences the system needs
    required_preferences = ["food", "pricerange", "area"]

    #only keep preferences that have not been provided
    missing = [
        slot for slot in required_preferences
        if preferences[slot] is None
    ]

    return missing


def ask_for_missing_preference(dialogue):
    missing = get_missing_preferences(dialogue["preferences"])

    #if nothing is missing, no question to ask
    if not missing:
        dialogue["current_slot"] = None
        return None

    #pick 1 of the missing preferences
    slot = random.choice(missing)
    dialogue["current_slot"] = slot
    
    return QUESTIONS[slot]


#safe the preferences
def update_preferences(dialogue, user_text):
    extracted = extract_slots(
        user_text,
        ONTOLOGY,
        current_slot=dialogue.get("current_slot")
    )

    #update when preference identified in the sentence
    dialogue["preferences"].update(extracted)

    return extracted


#remember the last response of the system if the user asks to repeat
def remember_last_response(dialogue, response):
    dialogue["last_system_response"] = response
    return dialogue["state"], response


def transition(dialogue, dialogue_act, user_text=""):
    state = dialogue["state"]

    #state 1: greet user
    if dialogue["state"] == GREET:
        dialogue["state"] = COLLECT_PREFERENCES

        return remember_last_response( 
            dialogue,
            "Hello! You can ask me for restaurants by food type, \n"
            "price range, or area. What are you looking for?"
        )

    #End conversation if the user says goodbye
    if dialogue_act == "bye":
        dialogue["state"] = END
        return remember_last_response(dialogue, "Goodbye! Have a nice day.")

    #let the user repeat the current prompt
    if dialogue_act == "repeat":
        return (
            dialogue["state"],
            dialogue["last_system_response"]
        )
    
    #if restarting, keep the loaded restaurants
    if dialogue_act == "restart":
        restaurants = dialogue["restaurants"]
        dialogue.clear()
        dialogue.update(create_dialogue())
        dialogue["restaurants"] = restaurants
        return transition(dialogue, "Hello again")

    #collect preferences
    if dialogue["state"] == COLLECT_PREFERENCES:
        if dialogue_act in {"inform", "hello", "reqalts", "confirm"}:
            #make sure users answer is stored before asking anything so questions are not repeated
            update_preferences(dialogue, user_text)
        
        question = ask_for_missing_preference(dialogue)

        if question is not None:
            dialogue["last_system_response"] = question
            return dialogue["state"], question

        #all preferences are known
        dialogue["state"] = ASK_EXTRA_REQUIREMENTS

        return remember_last_response(
            dialogue,
            "Do you have any extra requirements, such as wanting \n"
            "a romantic restaurant or one suitable for children?"
        )

    #extra requirements
    if dialogue["state"] == ASK_EXTRA_REQUIREMENTS:
        text = user_text.lower().strip()
        
        #Need to implement this
        if text != "no":
            return remember_last_response(
                dialogue,
                "not yet implemented (so answer no for extra requirements)"
            )
         
        #If no restaurant found for recommendation yet   
        matches = find_matching_restaurants(
            dialogue["restaurants"],
            dialogue["preferences"]
        )
        if not matches:
            dialogue["restaurant"] = None
            dialogue["state"] = COLLECT_PREFERENCES
            dialogue["preferences"]["food"] = None
            dialogue["current_slot"] = "food"
            
            #if no match for a restaurant
            return remember_last_response(
                dialogue,
                "Those preferences are not matches by any of the restaurants \n"
                "What other type of food would be to your liking"
            )
        #choose one of the matching restaurants randomly
        restaurant = random.choice(matches)
        dialogue["restaurant"] = restaurant
        #store all other not randomly picked restaurants so they can be picked as alternatives
        remaining_restaurants = []
        for possibilities in matches:
            if possibilities["restaurantname"] != restaurant["restaurantname"]:
                remaining_restaurants.append(possibilities)
        dialogue["remaining_restaurants"] = remaining_restaurants
        
        #change state if restaurant is picked
        dialogue["state"] = RECOMMEND
        
        #return recommendation
        return remember_last_response(
            dialogue,
            f"I would recommend {restaurant["restaurantname"]} which is located in the {restaurant["area"]}. \n"
            f"the price range is {restaurant["pricerange"]} and it is an {restaurant["food"]} restaurant. \n"
        )
        
        
    if dialogue["state"] == RECOMMEND:
        restaurant = dialogue["restaurant"]
        text = user_text.lower().strip()
        
        #first see if preferences change --> added because 20 reference dialogs do this
        if dialogue_act in {"inform", "reqalts", "reqmore"}:
            extracted = extract_slots(user_text, ONTOLOGY, current_slot=None)
            changed_list = []
            for slot, value in extracted.items():
                if dialogue["preferences"][slot] != value:
                    changed_list.append(dialogue["preferences"][slot])
            #changed is true only if any changes have been made in preference
            changed = len(changed_list) > 0 
            
            #and if there have been made changes make new list of 
            # restaurants and remaining restaurants 
            if changed:
                dialogue["preferences"].update(extracted)
                matches = find_matching_restaurants(dialogue["restaurants"], dialogue["preferences"])
                
                dialogue["restaurant"]=None
                dialogue["remaining_restaurants"] = []
                #if no matches for nu preference, let user type new preference
                if not matches:
                    return remember_last_response(
                                dialogue,
                                "Those new preferences are not matches by any of the restaurants \n"
                                "Please change, food, area, or price range"
                            )
                #choose a random restaurant from the matches again 
                # and put the rest in remaining_restaurants
                restaurant = random.choice(matches)
                dialogue["restaurant"] = restaurant
                remaining_restaurants = []
                for possibilities in matches:
                    if possibilities["restaurantname"] != restaurant["restaurantname"]:
                        remaining_restaurants.append(possibilities)
                dialogue["remaining_restaurants"] = remaining_restaurants
                
                #return updated recommendation
                return remember_last_response(
                    dialogue,
                    f"I would recommend {restaurant["restaurantname"]} which is located in the {restaurant["area"]}. \n"
                    f"the price range is {restaurant["pricerange"]} and it is an {restaurant["food"]} restaurant. \n"
                )
        
        #handle a request for another restaurant
        if dialogue_act in {"reqalts", "reqmore"}: 
            rest = dialogue["remaining_restaurants"]
            #handle the case when there is no other restaurant match for the preferences
            if not rest:
                return remember_last_response(
                    dialogue,
                    "There are no other restaurants which match \n"
                    "your current preferences"
                )
            #choose another restaurant from the remaining matches randomly 
            #and remove that recommendation from the remaining restaurants
            restaurant = random.choice(rest)
            rest.remove(restaurant)
            
            dialogue["restaurant"] = restaurant
            
            #again, return recommendation
            return remember_last_response(
                        dialogue,
                        f"I would recommend {restaurant["restaurantname"]} which is located in the {restaurant["area"]}. \n"
                        f"the price range is {restaurant["pricerange"]} and it is an {restaurant["food"]} restaurant. \n"
                    )
        
        #add all contact details if they are in the users request
        users_requests = []
        
        if ("phone" in text or "number" in text or "telephone" in text):
            users_requests.append(("phone", "phone number"))
        if "address" in text:
            users_requests.append(("addr", "adress"))
        if ("post code" in text or "postcode" in text or "postal code" in text):
            users_requests.append(("postcode", "postcode"))
        
        #now start making the answers for the users request
        if users_requests:
            #first handle the case when there is no recommendation for the request
            restaurant = dialogue["restaurant"]
            if restaurant is None:
                return remember_last_response(
                    dialogue,
                    "There is no recommendation. \n"
                    "Please change one of the preferences"
                )
            
            responses_to_request = []
            #Add description to responses and put "unknown" if it is not there    
            for request, description in users_requests:
                answer = restaurant.get(request) or "unknown"
                responses_to_request.append(
                    f"the {description} of the restaurant {restaurant["restaurantname"]} "
                    f"is: {answer}"
                )
            #return the answers to the details of the restaurant
            #this way multiple requests at once are handled
            return remember_last_response(
                dialogue,
                "".join(responses_to_request)
            )
        
        return remember_last_response(
            dialogue,
            "You can ask for the details of the phone number, \n"
            "address or postcode. or say goodbye"
        )

    #Last resort
    return remember_last_response(
        dialogue,
        "I'm sorry, I didn't understand that."
        )
