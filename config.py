"""Configuration settings for the Sports Meet Management System"""

# Event types and their corresponding data entry fields
EVENT_TYPES = {
    "Running": "time",
    "Throwing": "distance", 
    "Jumping": "distance"
}

# Default point allocation system (can be customized per event)
DEFAULT_POINT_ALLOCATION = {
    1: 10,  # 1st place
    2: 8,   # 2nd place
    3: 6,   # 3rd place
    4: 5,   # 4th place
    5: 4,   # 5th place
    6: 3,   # 6th place
    7: 2,   # 7th place
    8: 1    # 8th place
}

# House names with their corresponding colors
HOUSES = ["Ignis", "Nereus", "Ventus", "Terra"]

# House color mapping
HOUSE_COLORS = {
    "Ignis": "#ff6b6b",    # Red
    "Nereus": "#4ecdc4",   # Blue
    "Ventus": "#fce38a",   # Yellow
    "Terra": "#95e1d3"     # Green
}

# Event categories with sample events
EVENTS = {
    "Running": [
        {"name": "100m Sprint", "unit": "seconds"},
        {"name": "200m Sprint", "unit": "seconds"},
        {"name": "400m Run", "unit": "seconds"},
        {"name": "800m Run", "unit": "minutes:seconds"},
        {"name": "1500m Run", "unit": "minutes:seconds"}
    ],
    "Throwing": [
        {"name": "Shot Put", "unit": "meters"},
        {"name": "Discus", "unit": "meters"},
        {"name": "Javelin", "unit": "meters"},
        {"name": "Hammer Throw", "unit": "meters"}
    ],
    "Jumping": [
        {"name": "Long Jump", "unit": "meters"},
        {"name": "High Jump", "unit": "meters"},
        {"name": "Triple Jump", "unit": "meters"},
        {"name": "Pole Vault", "unit": "meters"}
    ]
}

# Streamlit page configuration
PAGE_CONFIG = {
    "page_title": "Sports Meet Manager",
    "page_icon": "🏃‍♂️",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}