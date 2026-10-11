#get other restaurant properties fromm the 6 rules as defined in the assignment
def infer_requirements(restaurant):

    ##get relevant restaurant info & standardize text
    price_range = restaurant.get("pricerange", "").strip().lower()
    food = restaurant.get("food", "").strip().lower()
    food_quality = restaurant.get("food quality", "").strip().lower()
    crowdedness = restaurant.get("crowdedness", "").strip().lower()
    length_of_stay = restaurant.get("length of stay", "").strip().lower()

    #store the conclusions from each rule
    conclusions = {
        "touristic": [],
        "assigned seats": [],
        "children": [],
        "romantic": [],
    }

    #store the explanations for the applied rules
    explanations = []

        #6 reasoning rules:
    if price_range == "cheap" and food_quality == "good":
        conclusions["touristic"].append(True)
        explanations.append(
            "The restaurant is cheap and has good food, "
            "which suggests it attracts tourists."
        )

    if food == "romanian":
        conclusions["touristic"].append(False)
        explanations.append(
            "Romanian cuisine is considered less familiar to most tourists."
        )

    if crowdedness == "busy":
        conclusions["assigned seats"].append(True)
        explanations.append(
            "The restaurant is busy, so the waiter is expected to decide where guests sit."
        )

    if length_of_stay == "long":
        conclusions["children"].append(False)
        explanations.append(
            "A long stay is considered unsuitable when dining with children."
        )

    if crowdedness == "busy":
        conclusions["romantic"].append(False)
        explanations.append(
            "The restaurant is busy, which suggests it is not romantic."
        )

    if length_of_stay == "long":
        conclusions["romantic"].append(True)
        explanations.append(
            "A long stay is considered romantic."
        )

    #combine conclusions + identify possible contradictions
    requirements = {}
    conflicts = {}

    for property_name, values in conclusions.items():
        distinct_values = set(values)

        if len(distinct_values) == 1:
            requirements[property_name] = values[0]
        elif len(distinct_values) > 1:
            requirements[property_name] = None
            conflicts[property_name] = values

#return the inferred properties, explanations + conflicts
    return requirements, explanations, conflicts
