# MCX to ScrapLink commodity name & contract specification mapping

MCX_TO_SCRAPLINK = {
    # Industrial Metals (Symbol -> {name, category, lot_size_kg})
    "COPPER": {"name": "Copper", "category": "Metals", "lot_size_kg": 2500},
    "ALUMINIUM": {"name": "Aluminum", "category": "Metals", "lot_size_kg": 5000},
    "ALUMINI": {"name": "Aluminum", "category": "Metals", "lot_size_kg": 1000},
    "ZINC": {"name": "Zinc", "category": "Metals", "lot_size_kg": 5000},
    "ZINCMINI": {"name": "Zinc", "category": "Metals", "lot_size_kg": 1000},
    "LEAD": {"name": "Lead", "category": "Metals", "lot_size_kg": 5000},
    "LEADMINI": {"name": "Lead", "category": "Metals", "lot_size_kg": 1000},
    "NICKEL": {"name": "Nickel", "category": "Metals", "lot_size_kg": 1500},
    "STEELREBAR": {"name": "Steel", "category": "Metals", "lot_size_kg": 10000},
    "MCXMETLDEX": {"name": "Metals Index", "category": "Metals Index", "lot_size_kg": 1000},

    # Precious Metals
    "GOLD": {"name": "Gold", "category": "Precious Metals", "lot_size_kg": 1},
    "GOLDM": {"name": "Gold", "category": "Precious Metals", "lot_size_kg": 0.1},
    "GOLDGUINEA": {"name": "Gold", "category": "Precious Metals", "lot_size_kg": 0.008},
    "GOLDPETAL": {"name": "Gold", "category": "Precious Metals", "lot_size_kg": 0.001},
    "GOLDTEN": {"name": "Gold", "category": "Precious Metals", "lot_size_kg": 0.01},
    "SILVER": {"name": "Silver", "category": "Precious Metals", "lot_size_kg": 30},
    "SILVER100": {"name": "Silver", "category": "Precious Metals", "lot_size_kg": 0.1},
    "SILVERM": {"name": "Silver", "category": "Precious Metals", "lot_size_kg": 5},
    "SILVERMIC": {"name": "Silver", "category": "Precious Metals", "lot_size_kg": 1},
    "MCXBULLDEX": {"name": "Bullion Index", "category": "Bullion Index", "lot_size_kg": 10},

    # Energy
    "CRUDEOIL": {"name": "Crude Oil", "category": "Energy", "lot_size_kg": 100},
    "CRUDEOILM": {"name": "Crude Oil", "category": "Energy", "lot_size_kg": 10},
    "NATURALGAS": {"name": "Natural Gas", "category": "Energy", "lot_size_kg": 1250},
    "NATGASMINI": {"name": "Natural Gas", "category": "Energy", "lot_size_kg": 250},

    # Agro & Textiles
    "COTTON": {"name": "Cotton", "category": "Agro", "lot_size_kg": 4250},
    "COTTONCNDY": {"name": "Cotton", "category": "Agro", "lot_size_kg": 8500},
    "COTTONOIL": {"name": "Cotton", "category": "Agro", "lot_size_kg": 10000},
    "KAPAS": {"name": "Cotton", "category": "Agro", "lot_size_kg": 4000},
    "CARDAMOM": {"name": "Cardamom", "category": "Agro", "lot_size_kg": 100},
    "MENTHAOIL": {"name": "Mentha Oil", "category": "Agro", "lot_size_kg": 360},
    "ELECDMBL": {"name": "Electricity", "category": "Energy", "lot_size_kg": 1000},
}
