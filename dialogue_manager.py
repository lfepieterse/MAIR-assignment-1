import random
import re

from dialogue_state import(
    GREET,
    COLLECT_PREFERENCES,
    ASK_EXTRA_REQUIREMENTS,
    END,
    RECOMMEND,
    CONFIRM_PREFERENCE,
    create_dialogue
)
from slot_extraction import ONTOLOGY, extract_slots, suggest_correction, find_possible_misspellings
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
    slot = missing[0]
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


    #handle the contact detail requests
    text = user_text.lower().strip().rstrip(".,!?")

    users_requests = []

    if "phone" in text or "number" in text or "telephone" in text:
        users_requests.append(("phone", "phone number"))
    if "address" in text:
        users_requests.append(("addr", "address"))
    if any(term in text for term in ("post code", "postcode", "postal code")):
        users_requests.append(("postcode", "postcode"))

    if users_requests:
        restaurant = dialogue.get("restaurant")

        if restaurant is None:
            return remember_last_response(
                dialogue,
                "I can provide contact details after recommending a restaurant. "
                "Let's first find one that matches your preferences."
            )

        responses_to_request = []
        for request, description in users_requests:
            answer = restaurant.get(request) or "unknown"
            responses_to_request.append(
                f"The {description} of {restaurant['restaurantname']} is: {answer}"
            )

        return remember_last_response(
            dialogue,
            " ".join(responses_to_request)
        )

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
        return transition(dialogue, "hello", "Hello again")

    if dialogue["state"] == CONFIRM_PREFERENCE:
        text = user_text.lower().strip()
        #if user confirms the correction, store the correction
        if dialogue_act == "affirm" or text == "yes":
            pending = dialogue["pending_correction"]
            #substitute the new value for food, price or area
            dialogue["preferences"][pending["slot"]] = pending["value"]
        #if user does not affirm the correction, preferences stay the same
        elif dialogue_act == "negate" or text == "no":
            pass
        #let the user say yes or no
        else:
            return remember_last_response(
                dialogue,
                "Please say yes or no to confirm or deny"
            )
        #set pending correction to none and state to collect preferences
        dialogue["pending_correction"] = None
        dialogue["state"] = COLLECT_PREFERENCES
        
        #No returning value, because going into next state of collect_preference after this
        #"ack" so it is not treated as a preference
        dialogue_act = "ack"
        user_text = ""
        
    
    #collect preferences
    if dialogue["state"] == COLLECT_PREFERENCES:
        if dialogue_act in {"inform", "hello", "reqalts", "confirm"}:
            #make sure users answer is stored before asking anything so questions are not repeated
            extracted = update_preferences(dialogue, user_text)
            
            #This part handles misspellings
            #find a keyword match using the function from slot_extraction.py
            possibilities = find_possible_misspellings(user_text, dialogue["current_slot"])
            
            for slot, possibility in possibilities.items():
                #skip the slots that are already matched
                if slot in extracted:
                    continue
                correction = suggest_correction(possibility, ONTOLOGY[slot])
                
                #if there is a correction possibility, this value is stored 
                # before being confirmed. by user
                if correction is not None:
                    dialogue["pending_correction"] = {"slot": slot, "value": correction}
                    dialogue["state"] = CONFIRM_PREFERENCE
                    
                    #here the confirmation question is stored as last response
                    return remember_last_response(
                        dialogue,
                        f"Did you mean {correction} for {slot}?"
                    )
            
            
        #if no correction question was returned continue normally
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

        #remove the punctuation at the end
        text = text.rstrip(".,!?")

        
        
        #when the user has no extra requirements
        no_extra_requirements = {
            "no",
            "no thanks",
            "no thank you",
            "i don't care",
            "i dont care",
            "no preference",
            "none",
            "not really"
        }

        if text not in no_extra_requirements:
            return remember_last_response(
                dialogue,
                "Please say if you have any extra requirements, "
                "or say 'no' if you don't."
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
            
            f"I would recommend {restaurant['restaurantname']} which is located in the {restaurant['area']}. \n"

            f"the price range is {restaurant['pricerange']} and it is an {restaurant['food']} restaurant. \n"
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
                    f"I would recommend {restaurant['restaurantname']} which is located in the {restaurant['area']}. \n"
                    f"the price range is {restaurant['pricerange']} and it is an {restaurant['food']} restaurant. \n"
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
                        f"I would recommend {restaurant['restaurantname']} which is located in the {restaurant['area']}. \n"
                        f"the price range is {restaurant['pricerange']} and it is an {restaurant['food']} restaurant. \n"
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
