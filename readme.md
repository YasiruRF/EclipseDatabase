# 🏃‍♂️ Sports Meet Event Management System

A comprehensive web application for managing school sports meets, built with  **Streamlit** ,  **Supabase** , and  **Python** .

## ✨ Features

### 👥 Student Management

* Register students with Curtin ID, Bib ID, name, and house
* Search students by Bib ID for quick access
* View all registered students with filtering options
* House-based organization (Ignis, Nereus, Ventus, Terra)

### 🎯 Event Management

* Support for three event types:  **Running** ,  **Throwing** , **Jumping**
* Customizable point allocation system per event
* Pre-configured standard events (100m Sprint, Long Jump, Shot Put, etc.)
* Add custom events with flexible scoring

### 📝 Result Entry

* Quick student search by Bib ID with auto-population
* Smart result input based on event type:
  * Running events: Time in seconds or MM:SS format
  * Throwing/Jumping: Distance in meters
* Automatic position calculation and point assignment
* Real-time leaderboard updates

### 🏆 Results & Analytics

* **Results by Event Type** : View all running, throwing, or jumping results
* **Individual Event Results** : Detailed view with podium display
* **Search & Filter** : Find results across all events
* **Export to CSV** : Download results for external use

### 🏠 House Points System

* **Real-time Leaderboard** : Live house standings with metric cards
* **Analytics Dashboard** : Performance analysis with charts
* **Detailed Breakdown** : Points distribution by event
* **Visual Charts** : Bar charts, pie charts, and progress tracking

## 🏠 House System

The system uses four houses with distinct colors and themes:

* **🔥 Ignis House** (Red) - Fire element
* **🌊 Nereus House** (Blue) - Water element
* **💨 Ventus House** (Yellow) - Air element
* **🌍 Terra House** (Green) - Earth element

## 🚀 Quick Start

### 1. Prerequisites

```bash
pip install streamlit supabase pandas plotly python-dotenv
```

### 2. Supabase Setup

1. Create a new Supabase project at [supabase.com](https://supabase.com/)
2. Run the SQL script from `database_setup.sql` in your Supabase SQL editor
3. Note your project URL and anon key

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

Or for Streamlit Cloud deployment, add these to your app secrets.

### 4. Run the Application

```bash
streamlit run main.py
```

## 📁 Project Structure

```
sports-meet-manager/
├── main.py                 # Main Streamlit application
├── config.py              # Configuration settings
├── database.py            # Supabase database operations
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── database_setup.sql     # Database schema and setup
├── .env.example          # Environment variables template
└── pages/                # Page modules
    ├── student_management.py
    ├── event_entry.py
    ├── results_view.py
    └── house_points.py
```

## 🎨 User Interface

### Navigation

* **Students Tab** : Manage student registrations and search
* **Event Entry Tab** : Record event results with smart input validation
* **Results Tab** : View and analyze results across all events
* **House Points Tab** : Live leaderboard and detailed analytics

### Key UI Features

* **Responsive Design** : Works on desktop and mobile devices
* **Real-time Updates** : Live data refresh without page reload
* **Visual Feedback** : Success/error messages and progress indicators
* **Export Options** : Download results as CSV files
* **Search & Filter** : Advanced filtering across all data views

## 🗄️ Database Schema

### Tables

#### `students`

| Column     | Type             | Description                                  |
| ---------- | ---------------- | -------------------------------------------- |
| curtin_id  | VARCHAR (PK)     | Student's Curtin University ID               |
| bib_id     | INTEGER (UNIQUE) | Race bib number                              |
| first_name | VARCHAR          | Student's first name                         |
| last_name  | VARCHAR          | Student's last name                          |
| house      | VARCHAR          | House assignment (Ignis/Nereus/Ventus/Terra) |
| created_at | TIMESTAMP        | Registration timestamp                       |

#### `events`

| Column           | Type        | Description                     |
| ---------------- | ----------- | ------------------------------- |
| event_id         | SERIAL (PK) | Unique event identifier         |
| event_name       | VARCHAR     | Name of the event               |
| event_type       | VARCHAR     | Type (Running/Throwing/Jumping) |
| unit             | VARCHAR     | Measurement unit                |
| point_allocation | JSONB       | Custom point scoring system     |
| created_at       | TIMESTAMP   | Event creation timestamp        |

#### `results`

| Column       | Type         | Description              |
| ------------ | ------------ | ------------------------ |
| result_id    | SERIAL (PK)  | Unique result identifier |
| curtin_id    | VARCHAR (FK) | Reference to student     |
| event_id     | INTEGER (FK) | Reference to event       |
| result_value | DECIMAL      | Performance result       |
| points       | INTEGER      | Points earned            |
| position     | INTEGER      | Final position/rank      |
| created_at   | TIMESTAMP    | Result entry timestamp   |

## ⚙️ Configuration

### Point System

Default point allocation (customizable per event):

* 1st place: 10 points
* 2nd place: 8 points
* 3rd place: 6 points
* 4th place: 5 points
* 5th place: 4 points
* 6th place: 3 points
* 7th place: 2 points
* 8th place: 1 point

### Event Types

* **Running** : Results in time (seconds), lower is better
* **Throwing** : Results in distance (meters), higher is better
* **Jumping** : Results in distance/height (meters), higher is better

### Houses

* **Ignis House** (Fire/Red) 🔥
* **Nereus House** (Water/Blue) 🌊
* **Ventus House** (Air/Yellow) 💨
* **Terra House** (Earth/Green) 🌍

## 🔧 Customization

### Adding New Event Types

1. Update `EVENT_TYPES` in `config.py`
2. Modify result input logic in `pages/event_entry.py`
3. Update ranking logic in `database.py`

### Changing Point System

* Modify `DEFAULT_POINT_ALLOCATION` in `config.py`
* Or set custom points per event through the UI

### Modifying Houses

1. Update `HOUSES` list in `config.py`
2. Update `HOUSE_COLORS` mapping in `config.py`
3. Update database constraints in `database_setup.sql`

## 🚀 Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Connect repository to [share.streamlit.io](https://share.streamlit.io/)
3. Add Supabase credentials to app secrets
4. Deploy!

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Run application
streamlit run main.py
```

## 📊 Analytics Features

### Performance Tracking

* Points distribution by event type
* Average points per house
* Participation rates
* Podium finish tracking

### Visual Analytics

* Real-time bar charts for house competition
* Pie charts for performance distribution
* Progress tracking with metric cards
* Color-coded house representation

### Export Capabilities

* Individual event results
* Complete results dataset
* House points summary
* Filtered search results

## 🛡️ Data Validation

### Input Validation

* Curtin ID: 8-digit format validation
* Bib ID: Unique positive integer
* Names: Non-empty string validation
* Results: Positive numeric values
* Time Format: MM:SS or seconds validation
* House: Must be one of the four valid houses

### Database Constraints

* Primary key constraints
* Foreign key relationships
* Check constraints for data integrity
* Unique constraints to prevent duplicates
* House validation (Ignis, Nereus, Ventus, Terra only)

## 🔄 Automatic Features

### Real-time Updates

* Position recalculation on new results
* Points redistribution when rankings change
* Live leaderboard updates
* Automatic sorting by performance

### Smart Ranking

* Event-specific sorting (time vs distance)
* Tie-breaking mechanisms
* Position gap handling
* Points allocation based on final position

## 🎯 Best Practices

### Data Entry

1. Register all students before events begin
2. Use consistent Bib ID numbering
3. Double-check results before submission
4. Regularly export data backups

### Event Management

1. Set up events before the sports meet
2. Test point allocation systems
3. Configure custom scoring if needed
4. Verify event types and units

### System Administration

1. Monitor database performance
2. Regular data backups
3. Check for data inconsistencies
4. Update dependencies regularly

## 📄 License

This project is open source and available under the [MIT License](https://claude.ai/chat/LICENSE).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:

* Create an issue on GitHub
* Check the documentation
* Review the SQL setup guide
* Verify Supabase connection

---

Built with ❤️ using Streamlit and Supabase
