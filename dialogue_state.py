#main system states
GREET = "greeting"
COLLECT_PREFERENCES = "collect_preferences"
ASK_EXTRA_REQUIREMENTS = "ask_extra_requirements"
COLLECT_EXTRA_REQUIREMENTS = "collect_extra_requirements"
PROVIDE_DETAILS = "provide_details"
RECOMMEND = "recommend"
END = "end"
CONFIRM_PREFERENCE = "confirm_preference"
RESOLVE_CONFLICT = "resolve_conflict"

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
        "remaining_restaurants": [], #store unused matches when user wants another recommendation
        "pending_correction": None, #whether there was a mispelling for which a correction needs approval
        
        #track conflicts
        "pending_conflicts": [],
        "pending_conflict_restaurant": None,
        "pending_conflict_property": None,
        "conflict_resolutions": {}
    }