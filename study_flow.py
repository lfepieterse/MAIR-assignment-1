"""Small, testable rules for the two-round study."""


def chatbot_order(participant_number):
    if participant_number < 1:
        raise ValueError("Participant numbers must start at 1.")
    if participant_number % 2 == 1:
        return ["formal", "friendly"]
    return ["friendly", "formal"]


def record_recommendation(round_data, before_state, before_name,
                          dialogue, recommend_state):
    restaurant = dialogue.get("restaurant") or {}
    name = restaurant.get("restaurantname")

    # Existing managers set RECOMMEND when a recommendation is completed.
    # Details and repetition leave the selected restaurant unchanged.
    newly_selected = name != before_name or before_state != recommend_state
    if (dialogue["state"] == recommend_state and name and newly_selected
            and name not in round_data["restaurants"]):
        round_data["restaurants"].append(name)
        return True
    return False
