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
        "extra_requirements": {},
        "restaurant": None,
        "current_slot": None,
        "last_system_response": "",
    }