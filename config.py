"""Configuration settings for the Sports Meet Management System - Gender-Specific Points & Bib ID Primary Key"""

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

# GENDER-SPECIFIC point allocation for individual events
# Individual Events: 1st=10, 2nd=6, 3rd=3, 4th=1 (same for both male and female)
DEFAULT_INDIVIDUAL_POINTS_MALE = {
    1: 10, 2: 6, 3: 3, 4: 1
}

DEFAULT_INDIVIDUAL_POINTS_FEMALE = {
    1: 10, 2: 6, 3: 3, 4: 1
}

# Relay events point allocation (teams compete together regardless of gender)
# Relay Events: 1st=15, 2nd=9, 3rd=5, 4th=3
DEFAULT_RELAY_POINTS = {
    1: 15, 2: 9, 3: 5, 4: 3
}

# Legacy - kept for backward compatibility
DEFAULT_INDIVIDUAL_POINTS = DEFAULT_INDIVIDUAL_POINTS_MALE

# Point system templates with gender-specific options
POINT_SYSTEM_TEMPLATES = {
    "Individual Events - Male": DEFAULT_INDIVIDUAL_POINTS_MALE,
    "Individual Events - Female": DEFAULT_INDIVIDUAL_POINTS_FEMALE,
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

# Gender-specific competition rules
COMPETITION_RULES = {
    "individual_events": {
        "description": "Individual events have separate male and female competitions",
        "scoring": "Males compete against males, females compete against females",
        "points": "Same point structure for both genders (10-6-3-1)"
    },
    "relay_events": {
        "description": "Relay teams can be mixed-gender and compete in single category",
        "scoring": "All teams compete together regardless of member genders",
        "points": "Single point structure for all teams (15-9-5-3)"
    }
}

# Database configuration
DATABASE_CONFIG = {
    "primary_key": "bib_id",  # Changed from curtin_id to bib_id
    "student_identifier": "bib_id",
    "unique_constraints": ["bib_id", "curtin_id"],
    "foreign_key_field": "bib_id"
}

# Event types with their scoring methods
EVENT_TYPES = {
    "Track": {
        "description": "Time-based events (running, hurdles, relays)",
        "unit": "seconds",
        "scoring_method": "lower_is_better",
        "display_format": "time"
    },
    "Field": {
        "description": "Distance/height-based events (jumping, throwing)",
        "unit": "meters", 
        "scoring_method": "higher_is_better",
        "display_format": "distance"
    }
}

# Gender-specific ranking configuration
RANKING_CONFIG = {
    "individual_events": {
        "separate_by_gender": True,
        "male_points": DEFAULT_INDIVIDUAL_POINTS_MALE,
        "female_points": DEFAULT_INDIVIDUAL_POINTS_FEMALE
    },
    "relay_events": {
        "separate_by_gender": False,
        "mixed_points": DEFAULT_RELAY_POINTS
    }
}

# System validation rules
VALIDATION_RULES = {
    "bib_id": {
        "type": "integer",
        "min_value": 1,
        "max_value": 9999,
        "unique": True
    },
    "curtin_id": {
        "type": "string",
        "pattern": r"^\d{8}$",
        "unique": True
    },
    "relay_team_size": 4,
    "max_events_per_student": None,  # No limit
    "required_fields": ["bib_id", "first_name", "last_name", "house", "gender"]
}