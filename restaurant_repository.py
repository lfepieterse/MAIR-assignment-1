import csv

#load csv data from restaurant
def load_restaurants(path):
    with open(path, newline = '') as csvfile:
            return [
                {
                    key: (value or "").strip().lower()
                    for key, value in row.items()
                }
                for row in csv.DictReader(csvfile)
            ]

def find_matching_restaurants(restaurants, preferences):
    matches = []
    for restaurant in restaurants:
        is_match = True
        #break if restaurant is no match when there is a preference given
        for slot, preference in preferences.items():
            if preference != "dontcare":
                if restaurant[slot] != preference:
                    is_match = False
                    break
        #otherwise add restaurant as match
        if is_match:
            matches.append(restaurant)
        
        
    return matches