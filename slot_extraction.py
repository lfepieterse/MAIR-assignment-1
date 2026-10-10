from Levenshtein import distance
import random
import re

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


#this selects a closest word match, only if it is uniquely the closest. 
#It uses the Levenshtein distance as important as distance
# We chose to not use a maximum for distance and also choose a random spelling if two words
#have equall distances since the user would nontheless have to confirm the spelling
def suggest_correction(misspelling, posible_spellings):
    misspelling = misspelling.lower().strip()
    #if there is no misspelling or the list of possible corrections is empty skip
    if not misspelling or not posible_spellings:
        return None
    
    #uses Levenshtein to calculate the distance to the spellings
    distances = []
    for spelling in posible_spellings:
        distances.append((distance(misspelling, spelling), spelling))
    
    #choose the smallest spelling distance
    smallest_distance = min(dist for dist, value in distances)
    
    closest_spelling = []
    for function_distance, spelling in distances:
        if function_distance == smallest_distance:
            closest_spelling.append(spelling)
    
    #If there are multiple spellings equally close, choose 1
    if len(closest_spelling) != 1:
        return random.choice(closest_spelling)
    
    return closest_spelling[0]


#Function for the keyword matching using string operations
def find_possible_misspellings(user_text, current_slot = None):
    text = user_text.lower().strip()
    
    #replace any punctiation with a space
    for punctuation_signs in ".,?!;'":
        text = text.replace(punctuation_signs, " ")
        
    #word splitting 
    words = text.split()
    possibilities = {} #matching possibilities
    
    for place, word in enumerate(words):
        #if the word food is not the first word, use the word before that as possibility
        if word == "food" and place > 0:
            possibilities["food"] = words[place-1]
        
        #now look for area after the word "in" and possibly after "the"
        if word == "in":
            next_place = place + 1
            #make sure the next word is not the last word
            if next_place < len(words):
                if words[next_place] == "the":
                    next_place += 1 #if "in", then look at the word after that
                if next_place < len(words): #should not be bigger than length again
                    possibilities["area"] = words[next_place] #word after the is possible match
        
        #now for the price, look for words before price or priced
        if word in {"price", "priced"} and place > 0: #it should not be the first word
            possibilities["pricerange"] = words[place-1]
    
    #if the length of the input is only one word, take that word as possibility
    if current_slot is not None and len(words) == 1:
        possibilities[current_slot] = words[0]
    
    return possibilities