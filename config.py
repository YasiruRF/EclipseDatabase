"""Configuration settings for the Sports Meet Management System - Enhanced Version"""



# Track events (use time in MM:SS.ms format)
TRACK_EVENTS = [
    "100m Sprint", "200m Sprint", "400m Sprint", "800m Run", "1500m Run",
    "3000m Run", "100m Hurdles", "110m Hurdles", "400m Hurdles",
    "4x100m Relay", "4x400m Relay"
]

# Field events (use distance/height in meters)
FIELD_EVENTS = [
    "Long Jump", "High Jump", "Triple Jump", "Pole Vault",
    "Shot Put", "Discus Throw", "Javelin Throw", "Hammer Throw"
]

# Relay events (different point allocation)
RELAY_EVENTS = ["4x100m Relay", "4x400m Relay"]

# Default point allocation for individual events
DEFAULT_INDIVIDUAL_POINTS = {
    1: 10, 2: 8, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1
}

# Default point allocation for relay events (higher stakes)
DEFAULT_RELAY_POINTS = {
    1: 20, 2: 16, 3: 12, 4: 10, 5: 8, 6: 6, 7: 4, 8: 2
}

# Point system templates
POINT_SYSTEM_TEMPLATES = {
    "Individual Events": DEFAULT_INDIVIDUAL_POINTS,
    "Relay Events": DEFAULT_RELAY_POINTS,
    "Custom": {}
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



# Streamlit page configuration
PAGE_CONFIG = {
    "page_title": "Sports Meet Manager",
    "page_icon": "🏃‍♂️",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Gender options for individual athlete tracking
GENDER_OPTIONS = ["Male", "Female", "Other"]