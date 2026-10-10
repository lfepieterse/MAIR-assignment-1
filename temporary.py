from slot_extraction import find_possible_misspellings

print(
    find_possible_misspellings(
        "spenish food in the nort at a cheep price"
    )
)

print(find_possible_misspellings("spenish", "food"))
print(find_possible_misspellings("nort", "area"))
print(find_possible_misspellings("cheep", "pricerange"))