import random
import re

from dialogue_state import(
    GREET,
    COLLECT_PREFERENCES,
    ASK_EXTRA_REQUIREMENTS,
    END,
    RECOMMEND,
    CONFIRM_PREFERENCE,
    RESOLVE_CONFLICT,
    create_dialogue
)
from slot_extraction import ONTOLOGY, extract_slots, suggest_correction, find_possible_misspellings
from restaurant_repository import find_matching_restaurants
from reasoning import infer_requirements

#return requirements, explanations, & all conflicts

def find_restaurant_conflict(restaurant):

    requirements, explanations, conflicts = infer_requirements(restaurant)

    return requirements, explanations, conflicts


#ask user which option they prefer when a conflict occurss
def make_conflict_question(property_name, values):

    descriptions = {
        "touristic": {
            True: "a restaurant that attracts tourists",
            False: "a restaurant that is non-tourist",
        },
        "assigned seats": {
            True: "assigned seating",
            False: "no assigned seating",
        },
        "children": {
            True: "a restaurant suitable for children",
            False: "a restaurant less suitable for children",
        },
        "romantic": {
            True: "a romantic restaurant",
            False: "a less romantic restaurant",
        },
    }

    first_option = descriptions[property_name][values[0]]
    second_option = descriptions[property_name][values[1]]

    return (
        f"The available restaurants differ in their characteristics regarding {property_name}. "
        f"Which option do you prefer? "
        f"Choose between '{first_option}' and '{second_option}'."
    )


#store the conflicts & ask user aboutt the first conflict
def start_conflict_resolution(dialogue, restaurant, requirements, explanations, conflicts):

    dialogue["restaurant"] = restaurant
    dialogue["pending_conflicts"] = list(conflicts.items())
    dialogue["conflict_resolutions"] = {}
    dialogue["reasoning_explanations"] = explanations
    dialogue["inferred_requirements"] = requirements

    property_name, values = dialogue["pending_conflicts"].pop(0)
    dialogue["pending_conflict_property"] = property_name
    dialogue["pending_conflict_restaurant"] = restaurant

    dialogue["state"] = RESOLVE_CONFLICT

    return remember_last_response(
        dialogue,
        make_conflict_question(property_name, values)
    )

#check whether requirements match with user response:
def matches_conflict_choices(requirements, conflict_resolutions):

    for property_name, chosen_value in conflict_resolutions.items():
        inferred_value = requirements.get(property_name)

        #use selected preference of user
        if inferred_value is not None and inferred_value != chosen_value:
            return False

    return True

#another helper function to apply users conflict preferences
def apply_conflict_choices(requirements, conflict_resolutions):

    effective_requirements = requirements.copy()

    for property_name, chosen_value in conflict_resolutions.items():
        if effective_requirements.get(property_name) is None:
            effective_requirements[property_name] = chosen_value

    return effective_requirements

#helper function to check whether a restaurant matches user requirements

def matches_extra_requirements(restaurant, requirements):

    inferred_requirements, explanations, conflicts = infer_requirements(restaurant)

    for property_name, required_value in requirements.items():
        if required_value is None:
            continue

        #if the rules contradict each other -->do not reject the restaurant yet
        #dialogue can ask the user to resolve this conflict
        if property_name in conflicts:
            continue

        #known conclusion must agree with users preferrence
        inferred_value = inferred_requirements.get(property_name)

        if inferred_value is not None and inferred_value != required_value:
            return False

        #if no rule concludes anything about this property--> value is unknown (do not assume that unknown means unsuitable)

    return True




#helper to identify extra restaurant requirements in user response

def extract_extra_requirements(text):

    text = text.lower().strip()
    requirements = {}

    #romantic
    if any(phrase in text for phrase in [
        "not romantic", "less romantic", "non-romantic",
        "don't want a romantic", "do not want a romantic"
    ]):
        requirements["romantic"] = False
    elif "romantic" in text:
        requirements["romantic"] = True

    #suitable for children
    if any(phrase in text for phrase in [
        "not suitable for children", "not good for children",
        "not child-friendly", "no children"
    ]):
        requirements["children"] = False
    elif any(phrase in text for phrase in [
        "children", "child-friendly", "family-friendly"
    ]):
        requirements["children"] = True

    #assigned seats
    if any(phrase in text for phrase in [
        "no assigned seats", "without assigned seats",
        "no assigned seating"
    ]):
        requirements["assigned seats"] = False
    elif any(phrase in text for phrase in [
        "assigned seats", "assigned seating"
    ]):
        requirements["assigned seats"] = True

    #touristic
    if any(phrase in text for phrase in [
        "not touristic", "non-touristic", "not touristy",
        "non-touristy", "not a tourist"
    ]):
        requirements["touristic"] = False
    elif any(phrase in text for phrase in [
        "touristic", "touristy", "attracts tourists"
    ]):
        requirements["touristic"] = True

    return requirements




QUESTIONS = {
        "food": "What type of food do you prefer?",
        "pricerange": "What price range do you prefer: cheap, moderate, or expensive?",
        "area": "Which area do you prefer: north, south, east, west, or centre?"
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

#this just helps to generate the response for when explanations are asked
def response_for_recommendation(dialogue, restaurant, explanation):
    response = (
        f"I would recommend {restaurant['restaurantname']}, "
        f"located in the {restaurant['area']}. "
        f"The price range is {restaurant['pricerange']}, "
        f"and it is a {restaurant['food']} restaurant."
    )
    #if show reasoning is True, make sure the explanation is added to the recommendation
    if dialogue["show_reasoning"] and explanation:
        response += " " + explanation
    
    return remember_last_response(dialogue, response)
    

def transition(dialogue, dialogue_act, user_text=""):
    state = dialogue["state"]

    #state 1: greet user
    if dialogue["state"] == GREET:
        dialogue["state"] = COLLECT_PREFERENCES

        return remember_last_response( 
            dialogue,
            "I can help you find a restaurant based on food type, \n"
            "price range, or area. Tell me your preferences."
        )

    #End conversation if the user says goodbye
    if dialogue_act == "bye":
        dialogue["state"] = END
        return remember_last_response(dialogue, "Bye.")


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
                "I first need to find one that matches your preferences."
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
    
    #if restarting, keep configuration the same 
    if dialogue_act == "restart":
        restaurants = dialogue["restaurants"]
        show_reasoning = dialogue["show_reasoning"] #did user choose reasoning or not
        fallback_method = dialogue.get("fallback_method", "Levenshtein") #if spelling mistakes
        dialogue.clear()
        dialogue.update(create_dialogue())
        dialogue["restaurants"] = restaurants
        dialogue["show_reasoning"] = show_reasoning
        dialogue["fallback_method"] = fallback_method
        return transition(dialogue, "hello", "Hello again")

    
    #handling of user response to an reasoning conflict
    if dialogue["state"] == RESOLVE_CONFLICT:
        text = user_text.lower().strip().rstrip(".,!?")
        property_name = dialogue["pending_conflict_property"]

        descriptions = {
            "touristic": {
                True: ("tourist", "attracts tourists"),
                False: ("non-tourist", "not tourist", "less tourist"),
            },
            "assigned seats": {
                True: ("assigned seating", "assigned seats"),
                False: ("no assigned seating", "without assigned seats"),
            },
            "children": {
                True: ("suitable for children", "good for children"),
                False: ("less suitable for children", "not suitable for children"),
            },
            "romantic": {
                True: ("romantic",),
                False: ("less romantic", "non-romantic", "not romantic"),
            },
        }

        chosen_value = None

        #check for negative options to avoid matching part of a phrase (eg "less romantic" vs "romantic"))
        for value in (False, True):
            phrases = descriptions[property_name][value]
            if any(phrase in text for phrase in phrases):
                chosen_value = value
                break

        if chosen_value is None:
            return remember_last_response(
                dialogue,
                "Choose one of the two options in my previous question."
            )

        #get the user response for this restaurant
        dialogue["conflict_resolutions"][property_name] = chosen_value

        #ask about next conflict if there remains one
        if dialogue["pending_conflicts"]:
            next_property, next_values = dialogue["pending_conflicts"].pop(0)
            dialogue["pending_conflict_property"] = next_property

            return remember_last_response(
                dialogue,
                make_conflict_question(next_property, next_values)
            )

        #when all conflicts for this restaurant have been addressed
        restaurant = dialogue["pending_conflict_restaurant"]
        explanations = dialogue.get("reasoning_explanations", [])

        dialogue["pending_conflict_property"] = None
        dialogue["pending_conflict_restaurant"] = None
        
        #apply the user responses
        requirements = apply_conflict_choices(
            dialogue["inferred_requirements"],
            dialogue["conflict_resolutions"]
        )
        
        dialogue["inferred_requirements"] = requirements
        
        #keep the restaurant whose reasoning conflict the user resolved
        dialogue["restaurant"] = restaurant

        #store other restaurants that match the basic preferences
        matching_restaurants = [
            candidate
            for candidate in dialogue["restaurants"]
            if all(
                candidate.get(slot) == value
                for slot, value in dialogue["preferences"].items()
                if value is not None and value != "dontcare"
            )
            and candidate["restaurantname"] != restaurant["restaurantname"]
        ]

        dialogue["matching_restaurants"] = matching_restaurants
        dialogue["remaining_restaurants"] = matching_restaurants.copy()
        dialogue["state"] = RECOMMEND
                
        #remove explanations belonging to rules with conflicting conclusions
        conflicting_explanations = {
            "touristic": [
                "The restaurant is cheap and has good food, which suggests it attracts tourists.",
                "Romanian cuisine is considered less familiar to most tourists.",
            ],
            "romantic": [
                "The restaurant is busy, which suggests it is not romantic.",
                "A long stay is considered romantic.",
            ],
        }

        explanation_parts = [
            item
            for item in explanations
            if not any(
                item == conflicting_explanation
                for property_name in dialogue["conflict_resolutions"]
                for conflicting_explanation in conflicting_explanations.get(
                    property_name, []
                )
            )
        ]

        explanation = " ".join(explanation_parts)

        #explain to user how user response resolved conflicts
        choice_explanations = {
            "touristic": {
                True: "You chose a restaurant that attracts tourists.",
                False: "You chose the restaurant that is less likely to attract tourists.",
            },
            "romantic": {
                True: "You chose the restaurant classified as romantic.",
                False: "You chose the restaurant classified as less romantic.",
            },
        }

        for property_name, chosen_value in dialogue["conflict_resolutions"].items():
            explanation += " " + choice_explanations[property_name][chosen_value]


            return response_for_recommendation(dialogue, restaurant, explanation)
        
        return remember_last_response(
            dialogue,
            f"I've recorded your choices for "
            f"{restaurant['restaurantname']}. {explanation} "
            f"I recommend {restaurant['restaurantname']}, "
            f"located in the {restaurant['area']}. "
            f"The price range is {restaurant['pricerange']}, "
            f"and it is a {restaurant['food']} restaurant."
        )



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
                "Say yes or no to confirm or deny"
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
            "What additional requirements do you have? For example, \n"
            "preference for a romantic restaurant or one suitable for children. \n"
            "Enter YES if you have extra requirements or NO if you don't."
        )

    
    #extra requirements
    if dialogue["state"] == ASK_EXTRA_REQUIREMENTS:

        
        text = user_text.lower().strip().rstrip(".,!?")

        no_extra_requirements = {
            "no", "no thanks", "no thank you",
            "i don't care", "i dont care",
            "no preference", "none", "not really"
        }

        yes_answers = {"yes", "yes please", "yeah", "sure"}

        #collect requirements if response =  yes
        
        #ask for details when user says yes
        if text in {"yes", "yes please", "yeah", "sure"}:
            dialogue["awaiting_extra_requirements"] = True
            return remember_last_response(
                dialogue,
                "What extra requirements do you have? For example, "
                "a romantic restaurant or one suitable "
                "for children. It is possible to mention more than one."
            )


        #user can skip extra requirements:
        if text in no_extra_requirements:
            dialogue["extra_requirements"] = {}
            dialogue["awaiting_extra_requirements"] = False

        else:
            #accept requirements stated directly or after saying yes
            requirements = extract_extra_requirements(text)

            if not requirements:
                return remember_last_response(
                    dialogue,
                    "Tell me your extra requirements, such as "
                    "'romantic' or 'suitable for children', or say 'NO'"
                )

            #save the requirements for restaurant filtering
            dialogue["extra_requirements"] = requirements
            dialogue["awaiting_extra_requirements"] = False


        #find restaurants that match with the users basic preferences
        matches = find_matching_restaurants(
            dialogue["restaurants"],
            dialogue["preferences"]
        )

        #apply extra requirements when required
        extra_requirements = dialogue.get("extra_requirements", {})

        if extra_requirements:
            matches = [
                restaurant
                for restaurant in matches
                if matches_extra_requirements(
                    restaurant,
                    extra_requirements
                )
            ]


        if not matches:
            dialogue["restaurant"] = None
            dialogue["state"] = COLLECT_PREFERENCES
            dialogue["preferences"]["food"] = None
            dialogue["current_slot"] = "food"

            return remember_last_response(
                dialogue,
                "No restaurants match those preferences. "
                "What other type of food do you like?"
            )

        #check each matching restaurant for reasoning conflicts
        conflict_candidates = []

        for candidate in matches:
            requirements, explanations, conflicts = find_restaurant_conflict(
                candidate
            )

            #user preferences to resolve matching conflicts
            for property_name, preferred_value in dialogue.get(
                "extra_requirements", {}
            ).items():

                if property_name in conflicts:
                    #user has already told which option they prefer
                    requirements[property_name] = preferred_value
                    conflicts.pop(property_name)

            #ask the user only about conflicts they have not already resolved
            if conflicts:
                conflict_candidates.append(
                    (candidate, requirements, explanations, conflicts)
                )


        
        #ask for reasoning conflicts only when the user has extra requirements
        if dialogue.get("extra_requirements") and conflict_candidates:
            candidate, requirements, explanations, conflicts = random.choice(
                conflict_candidates
            )

            #keep other matching restaurants available for later
            dialogue["remaining_restaurants"] = [
                r for r in matches
                if r["restaurantname"] != candidate["restaurantname"]
            ]

            return start_conflict_resolution(
                dialogue,
                candidate,
                requirements,
                explanations,
                conflicts
            )


        #no conflicts: recommend some random matching restaurant
        restaurant = random.choice(matches)
        dialogue["restaurant"] = restaurant

        dialogue["remaining_restaurants"] = [
            r for r in matches
            if r["restaurantname"] != restaurant["restaurantname"]
        ]

        dialogue["state"] = RECOMMEND
        #now make sure it also works for explanations etc.
        requirements, explanations, conflicts= infer_requirements(restaurant) 
        explanation = " ".join(explanations)
        return response_for_recommendation(dialogue, restaurant, explanation)

        
        
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
                                "Change, food, area, or price range"
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
                    f"I recommend {restaurant['restaurantname']} located in the {restaurant['area']}. \n"
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
                        f"I recommend {restaurant['restaurantname']} located in the {restaurant['area']}. \n"
                        f"the price range is {restaurant['pricerange']} and it is an {restaurant['food']} restaurant. \n"
                    )
        
        
        
        return remember_last_response(
            dialogue,
            "You can ask for the restaurant's phone number, \n"
            "address or postcode. Or end this conversation by saying goodbye"
        )

    #Last resort
    return remember_last_response(
        dialogue,
        "I didn't understand that. Rephrase it."
        )
