"""Labelled dataset of 10 known-valid and known-invalid contradiction test cases."""

LABELLED_CONTRADICTIONS = [
    # 5 Known-Valid Contradictions (Clearly incompatible)
    {
        "id": "val-01",
        "description": "Footwear color mismatch",
        "quote": "I was wearing my finest polished brown leather brogues, fit for an admiral's deck.",
        "target": "Security cameras recorded a shadowy figure wearing bright canary-yellow boots fleeing the exhibit hall.",
        "expected": "VALID",
        "explanation": "Suspect claims brown brogues, camera records canary-yellow boots."
    },
    {
        "id": "val-02",
        "description": "Power blackout denial",
        "quote": "The chandeliers blazed like harbor lighthouses with uninterrupted electric splendor all night long.",
        "target": "The antiquities gallery main power and backup generator were abruptly severed at precisely 11:15 PM.",
        "expected": "VALID",
        "explanation": "Suspect claims uninterrupted lighting all night, power was severed at 11:15 PM."
    },
    {
        "id": "val-03",
        "description": "Store receipt presence",
        "quote": "I never dropped anchor at any terrestrial cutlery shop! I haven't set foot in any Spork Emporium.",
        "target": "A receipt from 'Spork Emporium' dated 10:45 PM that evening was recovered from the custodial break room bin.",
        "expected": "VALID",
        "explanation": "Suspect denies ever visiting Spork Emporium, but receipt from 10:45 PM was found in their bin."
    },
    {
        "id": "val-04",
        "description": "Arrival time conflict",
        "quote": "Pursuant to statutory truth, I was miles away in transit and never swiped any access credential prior to 9:00 AM!",
        "target": "The executive suite electronic badge reader logged Penelope's keycard scanning into the kitchen at 8:12 AM.",
        "expected": "VALID",
        "explanation": "Suspect claims arriving after 9:00 AM, keycard badge logged entry at 8:12 AM."
    },
    {
        "id": "val-05",
        "description": "Severe allergy denial vs physical residue",
        "quote": "I despise all floral aromas and have never possessed nor applied French lavender hand ointment in my entire existence!",
        "target": "A lavender scent of artisanal French lavender hand cream was discovered smeared on the espresso hopper lid.",
        "expected": "VALID",
        "explanation": "Suspect claims never using or possessing lavender ointment, lavender hand cream was left on the hopper."
    },

    # 5 Known-Invalid Contradictions (Compatible, irrelevant, or non-conflicting)
    {
        "id": "inv-01",
        "description": "General preference vs unrelated fact",
        "quote": "I enjoy drinking hot herbal tea before bed.",
        "target": "The antiquities gallery main power was abruptly severed at precisely 11:15 PM.",
        "expected": "INVALID",
        "explanation": "Drinking tea has no logical bearing on power line severance."
    },
    {
        "id": "inv-02",
        "description": "Compatible timing",
        "quote": "I was at home eating dinner at 7:00 PM.",
        "target": "The break-in alarm was triggered at 11:30 PM.",
        "expected": "INVALID",
        "explanation": "Being home at 7:00 PM does not conflict with an event at 11:30 PM."
    },
    {
        "id": "inv-03",
        "description": "Vague statement vs specific fact",
        "quote": "The museum is a large, venerable building with many historic rooms.",
        "target": "Security cameras recorded a shadowy figure wearing bright canary-yellow boots.",
        "expected": "INVALID",
        "explanation": "Acknowledging the museum's architecture does not contradict camera footage."
    },
    {
        "id": "inv-04",
        "description": "Wearing a coat vs wearing shoes",
        "quote": "I had on a heavy woolen overcoat to protect against the chilly night.",
        "target": "Security cameras recorded a shadowy figure wearing bright canary-yellow boots.",
        "expected": "INVALID",
        "explanation": "Wearing a heavy overcoat is completely compatible with wearing yellow boots."
    },
    {
        "id": "inv-05",
        "description": "Disliking coffee vs keycard scan",
        "quote": "I find the taste of roasted coffee beans bitter and uncouth.",
        "target": "The executive suite electronic badge reader logged Penelope's keycard scanning into the kitchen at 8:12 AM.",
        "expected": "INVALID",
        "explanation": "Disliking coffee does not preclude entering a kitchen."
    }
]
