#main system states
GREET = "greeting"
COLLECT_PREFERENCES = "collect_preferences"
ASK_EXTRA_REQUIREMENTS = "ask_extra_requirements"
COLLECT_EXTRA_REQUIREMENTS = "collect_extra_requirements"
PROVIDE_DETAILS = "provide_details"
RECOMMEND = "recommend"
END = "end"

def create_dialogue():
    return {
        "state": GREET,
        "preferences": {
            "food": None,
            "pricerange": None,
            "area": None
        },
        "extra_requirements": {},  #if extra requirements asked
        "restaurant": None,
        "current_slot": None, 
        "last_system_response": "", #if user asks to repeat
        "remaining_restaurants": [] #store unused matches when user wants another recommendation
    }