import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import uuid
import math
import datetime
import base64
from io import BytesIO

# Set page configuration
st.set_page_config(
    page_title="Scope 3 Emissions Calculator",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Haversine formula for accurate distance calculation
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

# Dictionary of city coordinates (Expanded Set)
CITY_COORDINATES = {
    "VELLORE": (12.9165, 79.1325),
    "CHENNAI": (13.0827, 80.2707),
    "DELHI": (28.6139, 77.2090),
    "MUMBAI": (19.0760, 72.8777),
    "LONDON": (51.5074, -0.1278),
    "NEW YORK": (40.7128, -74.0060),
    "AHMEDABAD": (23.0225, 72.5714),
    "BENGALURU": (12.9716, 77.5946),
    "HYDERABAD": (17.3850, 78.4867),
    "KOLKATA": (22.5726, 88.3639),
    "DUBAI": (25.276987, 55.296249),
    "PARIS": (48.8566, 2.3522),
    "TOKYO": (35.6762, 139.6503),
    "SYDNEY": (-33.8688, 151.2093),
    "SINGAPORE": (1.3521, 103.8198),
    "HONG KONG": (22.3193, 114.1694),
    "SAN FRANCISCO": (37.7749, -122.4194),
    "BERLIN": (52.5200, 13.4050),
    "TORONTO": (43.6532, -79.3832),
    "CAIRO": (30.0444, 31.2357)
}

# Enhanced Emission Factors (kg CO2e per km per passenger)
EMISSION_FACTORS = {
    "FLIGHT - ECONOMY": {
        "short_haul": 0.15,  # <800 km
        "medium_haul": 0.12, # 800-3700 km
        "long_haul": 0.09    # >3700 km
    },
    "FLIGHT - BUSINESS": {
        "short_haul": 0.30,
        "medium_haul": 0.24,
        "long_haul": 0.18
    },
    "FLIGHT - FIRST": {
        "short_haul": 0.45,
        "medium_haul": 0.36,
        "long_haul": 0.27
    },
    "TRAIN - STANDARD": 0.035,
    "TRAIN - HIGH SPEED": 0.05,
    "BUS - STANDARD": 0.04,
    "BUS - COACH": 0.03,
    "CAR - GASOLINE": 0.12,
    "CAR - DIESEL": 0.14,
    "CAR - HYBRID": 0.08,
    "CAR - ELECTRIC": 0.05,
    "TAXI": 0.15,
    "FERRY": 0.19
}

# Hotel emission factors (kg CO2e per night)
HOTEL_EMISSION_FACTORS = {
    "BUDGET": 15.0,
    "MID-RANGE": 25.0,
    "LUXURY": 40.0
}

# Meal emission factors (kg CO2e per meal)
MEAL_EMISSION_FACTORS = {
    "VEGAN": 1.5,
    "VEGETARIAN": 2.5,
    "OMNIVORE": 4.0
}

# Initialize session state variables
if "emissions_data" not in st.session_state:
    st.session_state.emissions_data = []
    st.session_state.total_emissions = 0.0
    st.session_state.trip_details = []
    st.session_state.transport_emissions = 0.0
    st.session_state.accommodation_emissions = 0.0
    st.session_state.meal_emissions = 0.0

def get_flight_emission_factor(distance, travel_class):
    """
    Returns the appropriate emission factor based on flight distance and class
    """
    if distance < 800:
        category = "short_haul"
    elif distance < 3700:
        category = "medium_haul"
    else:
        category = "long_haul"
    
    if travel_class == "FLIGHT - ECONOMY":
        return EMISSION_FACTORS["FLIGHT - ECONOMY"][category]
    elif travel_class == "FLIGHT - BUSINESS":
        return EMISSION_FACTORS["FLIGHT - BUSINESS"][category]
    else:
        return EMISSION_FACTORS["FLIGHT - FIRST"][category]

def calculate_distance(from_city, to_city):
    """
    Calculate distance between two cities using Haversine formula
    """
    coord1, coord2 = CITY_COORDINATES.get(from_city), CITY_COORDINATES.get(to_city)
    if coord1 and coord2:
        return round(haversine_distance(coord1[0], coord1[1], coord2[0], coord2[1]), 2)
    return 0

def get_download_link(df, filename, text):
    """
    Generate a download link for a dataframe
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def create_emissions_chart(transport_data, accommodation_data, meal_data):
    """
    Create emissions breakdown chart
    """
    total = sum([transport_data, accommodation_data, meal_data])
    
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = ['Transport', 'Accommodation', 'Meals']
    sizes = [transport_data/total*100, accommodation_data/total*100, meal_data/total*100]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    explode = (0.1, 0, 0)
    
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    ax.set_title('Emissions Breakdown')
    
    return fig

def create_transport_mode_chart(df):
    """
    Create a chart showing emissions by transport mode
    """
    transport_emissions = df.groupby('Mode')['Emission (kg CO2e)'].sum().reset_index()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette('viridis', len(transport_emissions))
    
    bars = ax.bar(transport_emissions['Mode'], transport_emissions['Emission (kg CO2e)'], color=colors)
    
    ax.set_ylabel('CO2e Emissions (kg)')
    ax.set_title('Emissions by Transport Mode')
    ax.set_xlabel('Transport Mode')
    
    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.1f}',
                ha='center', va='bottom', rotation=0)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    return fig

# Apply color theme
st.markdown(
    """
    <style>
        .stApp {
            background-color: #121212;
            color: white;
        }
        .css-1d391kg, .css-1v0mbdj, .css-qbe2hs {
            color: white !important;
        }
        .stDataFrame, .stTable {
            background-color: rgba(0, 0, 50, 0.8) !important;
            color: white !important;
        }
        .sidebar .sidebar-content {
            background-color: #1E1E1E;
            color: white;
        }
        .reportview-container .main .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-right: 2rem;
            padding-left: 2rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3 {
            color: #4CAF50;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .metric-container {
            background-color: rgba(10, 10, 60, 0.8);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #4CAF50;
        }
        .metric-label {
            font-size: 1rem;
            color: #aaa;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# App Header
col1, col2 = st.columns([1, 3])
with col1:
    st.image("https://via.placeholder.com/150?text=Eco+Calc", width=150)
with col2:
    st.title("Scope 3 Business Travel Emissions Calculator")
    st.markdown("*Calculate, track, and analyze your organization's business travel carbon footprint*")

st.markdown("---")

# Sidebar user details
with st.sidebar:
    st.header("User Details")
    
    user_type = st.radio("User Type", ["Internal Employee", "Guest"], horizontal=True)
    
    if user_type == "Internal Employee":
        employee_id = st.text_input("Employee ID")
        employee_name = st.text_input("Employee Name")
        department = st.selectbox("Department", ["Finance", "Marketing", "Operations", "R&D", "Sales", "IT", "HR", "Other"])
    else:
        employee_id = "Guest-" + str(uuid.uuid4())[:8]
        employee_name = st.text_input("Guest Name")
        department = "External"
    
    travel_purpose = st.selectbox("Travel Purpose", ["Client Meeting", "Conference", "Training", "Internal Meeting", "Project Work", "Other"])
    
    st.markdown("---")
    
    st.header("Date Range")
    start_date = st.date_input("Start Date", datetime.date.today())
    end_date = st.date_input("End Date", datetime.date.today() + datetime.timedelta(days=7))
    
    st.markdown("---")
    
    if st.session_state.emissions_data:
        st.subheader("Last Calculation")
        st.info(f"Total Emissions: {round(st.session_state.total_emissions, 2)} kg CO2e")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Transport", "Accommodation & Meals", "Reports"])

# Tab 1: Transport
with tab1:
    st.header("Transportation Details")
    
    num_trips = st.number_input("Number of Trips", min_value=1, max_value=20, step=1)
    
    trip_data = []
    
    for i in range(num_trips):
        st.subheader(f"Trip {i+1}")
        col1, col2 = st.columns(2)
        
        with col1:
            from_city = st.selectbox("From", sorted(list(CITY_COORDINATES.keys())), key=f"from_{i}")
            travel_mode = st.selectbox("Mode of Transport", 
                                       [mode for mode in EMISSION_FACTORS.keys() if isinstance(EMISSION_FACTORS[mode], (int, float)) or mode.startswith("FLIGHT")],
                                       key=f"mode_{i}")
        
        with col2:
            to_city = st.selectbox("To", sorted(list(CITY_COORDINATES.keys())), key=f"to_{i}")
            passengers = st.number_input("Number of Passengers", min_value=1, value=1, key=f"passengers_{i}")
        
        trip_distance = calculate_distance(from_city, to_city)
        st.info(f"Calculated Distance: {trip_distance} km")
        
        trip_data.append((from_city, to_city, travel_mode, passengers, trip_distance))

# Tab 2: Accommodation & Meals
with tab2:
    st.header("Accommodation & Meals")
    
    num_stays = st.number_input("Number of Overnight Stays", min_value=0, max_value=30, step=1)
    
    stay_data = []
    meal_data = []
    
    if num_stays > 0:
        for i in range(num_stays):
            st.subheader(f"Stay {i+1}")
            col1, col2 = st.columns(2)
            
            with col1:
                location = st.selectbox("Location", sorted(list(CITY_COORDINATES.keys())), key=f"loc_{i}")
                hotel_type = st.selectbox("Hotel Type", list(HOTEL_EMISSION_FACTORS.keys()), key=f"hotel_{i}")
            
            with col2:
                nights = st.number_input("Number of Nights", min_value=1, value=1, key=f"nights_{i}")
                
            stay_data.append((location, hotel_type, nights))
            
            st.subheader(f"Meals for Stay {i+1}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                breakfast = st.selectbox("Breakfast", list(MEAL_EMISSION_FACTORS.keys()) + ["None"], key=f"breakfast_{i}")
            with col2:
                lunch = st.selectbox("Lunch", list(MEAL_EMISSION_FACTORS.keys()) + ["None"], key=f"lunch_{i}")
            with col3:
                dinner = st.selectbox("Dinner", list(MEAL_EMISSION_FACTORS.keys()) + ["None"], key=f"dinner_{i}")
            
            meal_data.append((breakfast, lunch, dinner, nights))

# Tab 3: Reports
with tab3:
    st.header("Emissions Reports")
    
    if not st.session_state.emissions_data:
        st.info("No emissions data available yet. Please calculate emissions first.")
    else:
        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{round(st.session_state.transport_emissions, 2)}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Transport Emissions (kg CO2e)</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{round(st.session_state.accommodation_emissions, 2)}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Accommodation Emissions (kg CO2e)</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{round(st.session_state.meal_emissions, 2)}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Meal Emissions (kg CO2e)</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.subheader("Emissions Breakdown")
        breakdown_chart = create_emissions_chart(
            st.session_state.transport_emissions,
            st.session_state.accommodation_emissions,
            st.session_state.meal_emissions
        )
        st.pyplot(breakdown_chart)
        
        if st.session_state.trip_details:
            st.subheader("Transport Emissions by Mode")
            trip_df = pd.DataFrame(st.session_state.trip_details)
            transport_chart = create_transport_mode_chart(trip_df)
            st.pyplot(transport_chart)
        
        st.subheader("User Emissions History")
        history_df = pd.DataFrame(st.session_state.emissions_data)
        st.dataframe(history_df)
        
        st.markdown(get_download_link(history_df, 'emissions_data.csv', 'Download Emissions Data CSV'), unsafe_allow_html=True)

# Calculate and Submit button
calculate_col1, calculate_col2 = st.columns([3, 1])
with calculate_col2:
    if st.button("Calculate Emissions", use_container_width=True):
        # Reset the calculation totals
        transport_emissions = 0
        accommodation_emissions = 0
        meal_emissions = 0
        trip_details = []
        
        # Calculate transport emissions
        for from_city, to_city, travel_mode, passengers, distance in trip_data:
            if travel_mode.startswith("FLIGHT"):
                emission_factor = get_flight_emission_factor(distance, travel_mode)
            else:
                emission_factor = EMISSION_FACTORS[travel_mode]
            
            trip_emission = round((distance * emission_factor) / passengers, 2)
            transport_emissions += trip_emission
            
            trip_details.append({
                "From": from_city, 
                "To": to_city, 
                "Mode": travel_mode, 
                "Distance (km)": distance, 
                "Emission (kg CO2e)": trip_emission
            })
        
        # Calculate accommodation emissions
        for location, hotel_type, nights in stay_data:
            stay_emission = HOTEL_EMISSION_FACTORS[hotel_type] * nights
            accommodation_emissions += stay_emission
        
        # Calculate meal emissions
        for breakfast, lunch, dinner, nights in meal_data:
            daily_meal_emission = 0
            if breakfast != "None":
                daily_meal_emission += MEAL_EMISSION_FACTORS[breakfast]
            if lunch != "None":
                daily_meal_emission += MEAL_EMISSION_FACTORS[lunch]
            if dinner != "None":
                daily_meal_emission += MEAL_EMISSION_FACTORS[dinner]
            
            meal_emissions += daily_meal_emission * nights
        
        # Total emissions
        total_trip_emission = transport_emissions + accommodation_emissions + meal_emissions
        
        # Store the results in session state
        st.session_state.transport_emissions = transport_emissions
        st.session_state.accommodation_emissions = accommodation_emissions
        st.session_state.meal_emissions = meal_emissions
        st.session_state.trip_details = trip_details
        
        # Create entry for emissions data
        entry = {
            "Employee ID": employee_id,
            "Name": employee_name,
            "Department": department,
            "Purpose": travel_purpose,
            "Start Date": start_date.strftime("%Y-%m-%d"),
            "End Date": end_date.strftime("%Y-%m-%d"),
            "Transport Emissions": round(transport_emissions, 2),
            "Accommodation Emissions": round(accommodation_emissions, 2),
            "Meal Emissions": round(meal_emissions, 2),
            "Total Emissions": round(total_trip_emission, 2),
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Update session state
        st.session_state.emissions_data.append(entry)
        st.session_state.total_emissions += total_trip_emission
        
        # Display success message
        st.success(f"Emissions calculated successfully! Total: {round(total_trip_emission, 2)} kg CO2e")
        
        # Auto-switch to reports tab
        st.rerun()

# Footer
st.markdown("---")
st.markdown("© 2025 Scope 3 Emissions Calculator | Developed for sustainable business travel")
