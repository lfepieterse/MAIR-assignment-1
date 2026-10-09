

#possible values for each preference
ONTOLOGY = {
    "food": [
        "italian", "chinese", "indian", "british", "french",
        "thai", "spanish", "portuguese", "greek", "romanian",
        "korean", "japanese", "vietnamese", "turkish",
        "mexican", "mediterranean", "seafood", "bistro",
        "modern european"
    ],
    "pricerange": ["cheap", "moderate", "expensive"],
    "area": ["north", "south", "east", "west", "centre"]
}

#handle user input of somehting doesnt matter
def extract_slots(user_text, ontology, current_slot=None):
    text = user_text.lower().strip()
    extracted = {}

    #dont care examples
    dontcare_phrases = [
        "it doesn't matter",
        "it does not matter",
        "doesn't matter",
        "does not matter",
        "i don't mind",
        "i do not mind",
        "i do not care",
        "i don't care"
        "no preference",
        "any",
        "whatever"
    ]

    says_dontcare = any(
        phrase in text for phrase in dontcare_phrases
    )

    #if user has no preference, apply it to the slot the system most recently asked about
    if says_dontcare and current_slot is not None:
        extracted[current_slot] = "dontcare"

    #also find explicit values
    for slot, values in ontology.items():
        for value in sorted(values, key=len, reverse=True):
            if value in text:
                extracted[slot] = value
                break

    return extracted
