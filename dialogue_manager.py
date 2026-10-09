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


#remember the last response of the system
def remember_last_response(dialogue, response):
    dialogue["last_system_response"] == response
    return dialogue["state"], response


def transition(dialogue, dialogue_act, user_text=""):
    state = dialogue["state"]

    #state 1: greet user
    if dialogue["state"] == GREET:
        dialogue["state"] = COLLECT_PREFERENCES

        return remember_last_response( 
            dialogue,
            "Hello! You can ask me for restaurants by food type, "
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
            "Do you have any extra requirements, such as wanting "
            "a romantic restaurant or one suitable for children?"
        )

    #extra requirements
    if dialogue["state"] == ASK_EXTRA_REQUIREMENTS:
        text = user_text.lower().strip()
        
        if text != "no":
            return remember_last_response(
                dialogue,
                "not yet implemented (so answer no for extra requirements)"
            )
            
        matches = find_matching_restaurants(
            dialogue["restaurants"],
            dialogue["preferences"]
        )
        if not matches:
            dialogue["restaurant"] = None
            dialogue["state"] = COLLECT_PREFERENCES
            dialogue["preferences"]["food"] = None
            dialogue["current_slot"] = "food"
            
            return remember_last_response(
                dialogue,
                "Those preferences are not matches by any of the restaurants"
                "What other type of food would be to your liking"
            )
        restaurant = random.choice(matches)
        dialogue["restaurant"] = restaurant
        dialogue["state"] = RECOMMEND
        return remember_last_response(
            dialogue,
            f"I would recommend {restaurant["restaurantname"]},"
            f"the pricerange is {restaurant["pricerange"]}"
            f"and it is {restaurant["food"]}"
            f"located in the {restaurant["area"]}"
        )
        
        return remember_last_response(
            dialogue,
            "Please tell me your extra requirements, or say no "
            "if you don't have any."
        )
        
    if dialogue["state"] == RECOMMEND:
        remember_last_response(
            dialogue,
            "Say goodbye if you want to restart this conversation."
        )

    return remember_last_response(
        dialogue,
        "I'm sorry, I didn't understand that."
        )
