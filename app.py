import streamlit as st
from datetime import datetime, timedelta
import time
import re

from config import Config
from models import TravelType, TripRequest
from graph import run_trip_planner_stepwise
from langsmith_monitor import monitor



st.set_page_config(
    page_title="AI Trip Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    if 'trip_planned' not in st.session_state:
        st.session_state['trip_planned'] = False
    if 'final_state' not in st.session_state:
        st.session_state['final_state'] = None
    if 'planning_history' not in st.session_state:
        st.session_state['planning_history'] = []


def validate_config():
    try:
        Config.validate()
        return True
    except ValueError as e:
        st.error(f"⚠️ Configuration Error: {str(e)}")
        st.info("💡 Please set up your API keys in a .env file")
        return False

def format_travel_type(travel_type: str) -> str:
    travel_icons = {
        "relaxation": "🏖️ Relaxation",
        "adventure": "🏔️ Adventure",
        "sightseeing": "🏛️ Sightseeing",
        "business": "💼 Business",
        "family": "👨‍👩‍👧‍👦 Family"
    }
    return travel_icons.get(travel_type, travel_type.title() if travel_type else "Unknown")


def display_header():
    st.markdown("""
        <div style='text-align: center; padding: 1rem 0 2rem 0;'>
            <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>✈️ AI Trip Planner</h1>
            <p style='font-size: 1.2rem; color: #666;'>
                Plan your perfect trip with AI-powered recommendations
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("🌍 **Real-time Data**")
        st.caption("Live weather & flights")
    with col2:
        st.markdown("🤖 **AI-Powered**")
        st.caption("Smart recommendations")
    with col3:
        st.markdown("💰 **Budget-Aware**")
        st.caption("Optimize spending")
    with col4:
        st.markdown("📅 **Day-by-Day**")
        st.caption("Detailed itineraries")

    st.divider()

def trip_input_form():
    st.markdown("### 📝 Trip Details")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🗺️ Route Information")
        origin = st.text_input("Departure City", placeholder="e.g., New York", key="origin")
        destination = st.text_input("Destination", placeholder="e.g., Tokyo", key="destination")

        st.markdown("#### 📅 Travel Dates")
        start_date = st.date_input("Departure Date", value=datetime.now() + timedelta(days=30), min_value=datetime.now(), key="start_date")
        duration = st.number_input("Duration (days)", min_value=1, max_value=30, value=7, step=1, key="duration")

    with col2:
        st.markdown("#### 💰 Budget & Preferences")
        budget = st.number_input("Total Budget (USD)", min_value=500, max_value=50000, value=2000, step=100, key="budget")
        currency = st.selectbox("Currency", options=["USD", "EUR", "GBP", "JPY", "INR"], index=0, key="currency")
        travel_type = st.selectbox("Travel Style", options=[t.value for t in TravelType], format_func=format_travel_type, key="travel_type")
        num_travelers = st.number_input("Travelers", min_value=1, max_value=10, value=1, step=1, key="num_travelers")

    end_date = start_date + timedelta(days=duration)

    return {
        "origin": origin,
        "destination": destination,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "duration_days": duration,
        "budget": budget,
        "currency": currency,
        "travel_type": travel_type,
        "num_travelers": num_travelers,
        "preferences": []
    }

def display_weather_step(weather):
    """Display enhanced weather analysis with more details"""
    st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
            <h3 style='color: white; margin: 0;'>☁️ Step 1: Weather Analysis</h3>
        </div>
    """, unsafe_allow_html=True)

    if weather:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Temperature with color coding
            temp_color = "#ff6b6b" if weather.temperature > 30 else "#4dabf7" if weather.temperature < 10 else "#51cf66"
            temp_feel = "Warm" if weather.temperature > 25 else "Cool" if weather.temperature < 15 else "Pleasant"
            
            st.markdown(f"""
                <div style='text-align: center; padding: 1rem; background: white; 
                            border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <h2 style='margin: 0; color: {temp_color};'>{weather.temperature}°C</h2>
                    <p style='margin: 0.5rem 0 0 0; color: #666;'>Temperature</p>
                    <p style='margin: 0.25rem 0 0 0; font-size: 0.85rem; color: #999;'>{temp_feel}</p>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            # Condition with emoji
            condition_emoji = {
                "Clear": "☀️",
                "Clouds": "☁️",
                "Rain": "🌧️",
                "Snow": "❄️",
                "Thunderstorm": "⛈️",
                "Drizzle": "🌦️",
                "Mist": "🌫️",
                "Fog": "🌫️"
            }.get(weather.condition, "🌤️")
            
            st.markdown(f"""
                <div style='text-align: center; padding: 1rem; background: white; 
                            border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <h2 style='margin: 0; font-size: 2rem;'>{condition_emoji}</h2>
                    <p style='margin: 0.5rem 0 0 0; color: #666;'>{weather.condition}</p>
                    <p style='margin: 0.25rem 0 0 0; font-size: 0.85rem; color: #999;'>Condition</p>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            # Humidity with comfort level
            humidity_color = "#ff6b6b" if weather.humidity > 70 else "#51cf66"
            comfort = "High" if weather.humidity > 70 else "Low" if weather.humidity < 30 else "Moderate"
            
            st.markdown(f"""
                <div style='text-align: center; padding: 1rem; background: white; 
                            border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <h2 style='margin: 0; color: {humidity_color};'>{weather.humidity}%</h2>
                    <p style='margin: 0.5rem 0 0 0; color: #666;'>Humidity</p>
                    <p style='margin: 0.25rem 0 0 0; font-size: 0.85rem; color: #999;'>{comfort}</p>
                </div>
            """, unsafe_allow_html=True)

        with col4:
            # Status with recommendation
            status_color = "#51cf66" if weather.is_favorable else "#ff6b6b"
            status_text = "✅ Favorable" if weather.is_favorable else "⚠️ Unfavorable"
            recommendation = "Great for travel!" if weather.is_favorable else "Consider alternatives"
            
            st.markdown(f"""
                <div style='text-align: center; padding: 1rem; background: {status_color}; 
                            border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <h2 style='margin: 0; color: white; font-size: 1.5rem;'>{status_text}</h2>
                    <p style='margin: 0.5rem 0 0 0; color: white;'>Overall</p>
                    <p style='margin: 0.25rem 0 0 0; font-size: 0.85rem; color: rgba(255,255,255,0.9);'>
                        {recommendation}
                    </p>
                </div>
            """, unsafe_allow_html=True)
        
        # Additional weather information
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "💨 Wind Speed", 
                f"{weather.wind_speed} m/s",
                help="Average wind speed"
            )
        
        with col2:
            st.metric(
                "🌧️ Rain Chance", 
                f"{weather.precipitation_chance}%",
                help="Probability of precipitation"
            )
        
        with col3:
            # Clothing recommendation
            if weather.temperature > 25:
                clothing = "👕 Light clothing"
            elif weather.temperature > 15:
                clothing = "🧥 Light jacket"
            else:
                clothing = "🧥 Warm clothing"
            
            st.info(f"**What to wear:** {clothing}")

        if weather.alert:
            st.warning(f"⚠️ **Weather Alert:** {weather.alert}")
    else:
        st.info("Weather data not available")


def display_flight_card(flight, index):
    st.markdown(f"""
        <div style='background: white; padding: 1rem; border-radius: 10px; 
                    border-left: 4px solid #667eea; margin-bottom: 1rem;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <h4 style='margin: 0 0 0.5rem 0;'>✈️ {flight.airline}</h4>
                    <p style='margin: 0; color: #666;'>
                        🛫 {flight.departure_time} → 🛬 {flight.arrival_time}
                    </p>
                    <p style='margin: 0.25rem 0 0 0; color: #666; font-size: 0.9rem;'>
                        ⏱️ {flight.duration} • 🔄 {flight.stops} stop{"s" if flight.stops != 1 else ""}
                    </p>
                </div>
                <div style='text-align: right;'>
                    <h3 style='margin: 0; color: #667eea;'>${flight.price:,.0f}</h3>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def display_budget_breakdown(itinerary, hotels, flights, attractions):
    """Display detailed budget breakdown with visual bars"""
    import re
    
    # Calculate each component
    hotel_cost = sum(h.price_per_night for h in hotels[:1]) * len(itinerary.daily_plans) if hotels and itinerary.daily_plans else 0
    flight_cost = sum(f.price for f in flights[:1]) if flights else 0
    attraction_cost = sum(a.cost or 0 for a in attractions)
    
    # Calculate activity and meal costs
    activity_meal_cost = 0
    for day in itinerary.daily_plans:
        activities = day.get('activities', [])
        for activity in activities:
            cost_str = str(activity.get('estimated_cost', ''))
            matches = re.findall(r'\$([0-9]+)', cost_str)
            if matches:
                activity_meal_cost += int(matches[0])
        
        meals = day.get('meals', [])
        for meal in meals:
            cost_str = str(meal.get('estimated_cost', ''))
            matches = re.findall(r'\$([0-9]+)', cost_str)
            if matches:
                activity_meal_cost += int(matches[0])
    
    total_cost = hotel_cost + flight_cost + attraction_cost + activity_meal_cost
    
    st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <h3 style='color: white; margin: 0;'>💰 Detailed Budget Breakdown</h3>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Cost Components")
        
        # Flights with progress bar
        flight_pct = (flight_cost / total_cost * 100) if total_cost > 0 else 0
        st.markdown(f"**✈️ Flights**")
        st.progress(flight_pct / 100)
        st.caption(f"${flight_cost:,.2f} ({flight_pct:.1f}% of total)")
        
        # Hotels
        hotel_pct = (hotel_cost / total_cost * 100) if total_cost > 0 else 0
        st.markdown(f"**🏨 Accommodation**")
        st.progress(hotel_pct / 100)
        st.caption(f"${hotel_cost:,.2f} ({hotel_pct:.1f}% of total)")
        
        # Activities & Meals
        activity_pct = (activity_meal_cost / total_cost * 100) if total_cost > 0 else 0
        st.markdown(f"**🍽️ Activities & Meals**")
        st.progress(activity_pct / 100)
        st.caption(f"${activity_meal_cost:,.2f} ({activity_pct:.1f}% of total)")
        
        if attraction_cost > 0:
            attr_pct = (attraction_cost / total_cost * 100)
            st.markdown(f"**🎯 Attraction Fees**")
            st.progress(attr_pct / 100)
            st.caption(f"${attraction_cost:,.2f} ({attr_pct:.1f}% of total)")
    
    with col2:
        st.markdown("#### Summary")
        st.metric("💵 Total Budget", f"${itinerary.total_budget:,.2f}")
        st.metric("📊 Estimated Cost", f"${total_cost:,.2f}")
        
        savings = itinerary.total_budget - total_cost
        savings_pct = (savings / itinerary.total_budget * 100) if itinerary.total_budget > 0 else 0
        
        st.metric(
            "💰 Remaining Budget", 
            f"${savings:,.2f}",
            delta=f"{savings_pct:.1f}% saved"
        )
        
        daily_avg = total_cost / len(itinerary.daily_plans) if itinerary.daily_plans else 0
        st.metric("📅 Daily Average", f"${daily_avg:,.2f}")

def display_hotels_section(hotels, itinerary):
    """Display hotels section - ALL hotels shown"""
    st.markdown("""
        <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <h3 style='color: white; margin: 0;'>🏨 Accommodation Options</h3>
        </div>
    """, unsafe_allow_html=True)

    # ✅ Show ALL hotels (removed [:3] limit)
    for idx, hotel in enumerate(hotels, 1):
        # Expand first 3 by default
        with st.expander(f"**{idx}. {hotel.name}** ⭐ {hotel.rating}/5", expanded=(idx <= 3)):
            col1, col2 = st.columns([2, 1])

            with col1:
                if hotel.location:
                    st.markdown(f"**📍 Location:** {hotel.location}")
                if hotel.amenities:
                    st.markdown(f"**🎯 Amenities:** {', '.join(hotel.amenities)}")  # Show all
                if hotel.url:
                    st.markdown(f"**🔗 [Book Now]({hotel.url})**")
                if hotel.distance_from_center:
                    st.markdown(f"**📏 Distance:** {hotel.distance_from_center} km")

            with col2:
                nights = len(itinerary.daily_plans) if itinerary and itinerary.daily_plans else 7
                total = hotel.price_per_night * nights
                st.metric("Per Night", f"${hotel.price_per_night:.0f}")
                st.metric(f"Total ({nights}n)", f"${total:.0f}")


def display_attractions_section(attractions):
    """Display attractions section - handle None values"""
    st.markdown("""
        <div style='background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                    padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <h3 style='color: white; margin: 0;'>🎯 Top Attractions</h3>
        </div>
    """, unsafe_allow_html=True)

    cols = st.columns(2)
    for idx, attraction in enumerate(attractions):  # ✅ Show ALL attractions
        with cols[idx % 2]:
            # ✅ Handle None values
            rating_str = f"⭐ {attraction.rating}/5" if attraction.rating else "⭐ Rating N/A"
            time_str = f"⏱️ {attraction.estimated_time}" if attraction.estimated_time else "⏱️ Duration varies"
            cost_str = f"💵 ${attraction.cost:.0f}" if attraction.cost else "💵 Cost varies"

            st.markdown(f"""
                <div style='background: white; padding: 1rem; border-radius: 10px; 
                            margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <h4 style='margin: 0 0 0.5rem 0;'>{idx + 1}. {attraction.name}</h4>
                    <p style='margin: 0; color: #888; font-size: 0.9rem;'>📂 {attraction.category}</p>
                    <p style='margin: 0.5rem 0; color: #666;'>{attraction.description}</p>
                    <div style='display: flex; gap: 1rem; margin-top: 0.5rem; font-size: 0.9rem; color: #888;'>
                        <span>{rating_str}</span>
                        <span>{time_str}</span>
                        <span>{cost_str}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)



def display_itinerary_section(itinerary):
    st.markdown("""
        <div style='background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
                    padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <h3 style='color: #333; margin: 0;'>📅 Day-by-Day Itinerary</h3>
        </div>
    """, unsafe_allow_html=True)

    if not itinerary.daily_plans:
        st.info("No daily plans available")
        return

    for day_plan in itinerary.daily_plans:
        day_num = day_plan.get('day') if isinstance(day_plan, dict) else day_plan.day
        day_date = day_plan.get('date') if isinstance(day_plan, dict) else getattr(day_plan, 'date', 'TBD')
        
        # ✅ CALCULATE DAILY COST
        daily_cost = 0

        activities = day_plan.get('activities', []) if isinstance(day_plan, dict) else getattr(day_plan, 'activities', [])
        for activity in activities:
            if isinstance(activity, dict):
                cost_str = str(activity.get('estimated_cost', ''))
                matches = re.findall(r'\$([0-9]+)', cost_str)
                if matches:
                    daily_cost += int(matches[0])

        meals = day_plan.get('meals', []) if isinstance(day_plan, dict) else getattr(day_plan, 'meals', [])
        for meal in meals:
            if isinstance(meal, dict):
                cost_str = str(meal.get('estimated_cost', ''))
                matches = re.findall(r'\$([0-9]+)', cost_str)
                if matches:
                    daily_cost += int(matches[0])

        # ✅ SHOW DAY WITH COST IN HEADER
        with st.expander(
            f"**📆 Day {day_num}** - {day_date} • 💵 ~${daily_cost} estimated", 
            expanded=(day_num == 1)
        ):
            # Activities
            activities = day_plan.get('activities') if isinstance(day_plan, dict) else getattr(day_plan, 'activities', [])
            if activities:
                st.markdown("### 📍 Activities")
                for activity in activities:
                    if isinstance(activity, dict):
                        time = activity.get('time_of_day', '🕐 TBD')
                        desc = activity.get('description', 'Activity')
                        travel = activity.get('travel_time', '')
                        cost = activity.get('estimated_cost', '')

                        st.markdown(f"""
                            <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                                <strong style='color: #667eea;'>{time}</strong>
                                <p style='margin: 0.5rem 0;'>{desc}</p>
                                {"<p style='margin: 0; color: #888; font-size: 0.9rem;'>⏱️ " + travel + "</p>" if travel else ""}
                                {"<p style='margin: 0; color: #888; font-size: 0.9rem;'>💰 " + str(cost) + "</p>" if cost else ""}
                            </div>
                        """, unsafe_allow_html=True)

            # Meals
            meals = day_plan.get('meals') if isinstance(day_plan, dict) else getattr(day_plan, 'meals', [])
            if meals:
                st.markdown("### 🍽️ Meals")
                for meal in meals:
                    if isinstance(meal, dict):
                        meal_type = meal.get('type', 'Meal')
                        suggestion = meal.get('suggestion', '')
                        meal_cost = meal.get('estimated_cost', '')

                        icon = {"Breakfast": "🌅", "Lunch": "☀️", "Dinner": "🌙"}.get(meal_type, "🍴")

                        st.markdown(f"""
                            <div style='background: #fff8e1; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #ffc107;'>
                                <strong>{icon} {meal_type}</strong>
                                <p style='margin: 0.5rem 0 0 0;'>{suggestion}</p>
                                {"<p style='margin: 0.25rem 0 0 0; color: #888; font-size: 0.9rem;'>💵 " + str(meal_cost) + "</p>" if meal_cost else ""}
                            </div>
                        """, unsafe_allow_html=True)
            # ✅ DAILY COST SUMMARY
            st.markdown(f"""
                <div style='background: #e3f2fd; padding: 0.75rem; border-radius: 8px; margin-top: 1rem; border-left: 3px solid #2196f3;'>
                    <strong>📊 Day {day_num} Total: ~${daily_cost}</strong>
                    <p style='margin: 0.25rem 0 0 0; font-size: 0.9rem; color: #666;'>
                        Estimated cost for activities and meals
                    </p>
                </div>
            """, unsafe_allow_html=True)

            # Notes
            notes = day_plan.get('notes') if isinstance(day_plan, dict) else getattr(day_plan, 'notes', '')
            if notes:
                st.info(f"📝 **Tips:** {notes}")

def main():
    init_session_state()

    if not validate_config():
        st.stop()

    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        st.markdown(f"""
            <div style='background: #f8f9fa; padding: 0.5rem; border-radius: 5px; margin-bottom: 0.5rem;'>
                <strong>🤖 AI Model:</strong><br>
                <span style='color: #667eea;'>{Config.MODEL_NAME}</span>
            </div>
        """, unsafe_allow_html=True)
        
        langsmith_status = "✅ Enabled" if Config.LANGSMITH_API_KEY else "❌ Disabled"
        langsmith_color = "#51cf66" if Config.LANGSMITH_API_KEY else "#ff6b6b"
        st.markdown(f"""
            <div style='background: #f8f9fa; padding: 0.5rem; border-radius: 5px;'>
                <strong>📊 LangSmith:</strong><br>
                <span style='color: {langsmith_color};'>{langsmith_status}</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        if st.button("🔄 Start New Trip", use_container_width=True):
            st.session_state.trip_planned = False
            st.session_state.final_state = None
            st.rerun()
        
        st.divider()
        
        st.markdown("### 📚 About")
        st.markdown("""
            **Powered by:**
            - 🦜 LangChain
            - 🔗 LangGraph
            - 🤖 Gemini 2.5 Flash
            - 🌐 Real-time APIs
            
            **Features:**
            - Live weather data
            - Real flight prices
            - Budget optimization
            - Smart alternatives
        """)
        
        # Planning history
        if st.session_state.planning_history:
            st.divider()
            st.markdown("### 📜 Recent Plans")
            for entry in st.session_state.planning_history[-3:]:
                st.caption(f"🗺️ {entry['destination']}")

    display_header()

    if not st.session_state.trip_planned:
        trip_data = trip_input_form()

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            plan_button = st.button("🚀 Plan My Trip", type="primary", use_container_width=True)

        if plan_button:
            if not trip_data['origin']:
                st.error("❌ Please enter departure city")
            elif not trip_data['destination']:
                st.error("❌ Please enter destination")
            else:
                try:
                    trip_request = TripRequest(**trip_data)

                    progress_placeholder = st.empty()
                    status_placeholder = st.empty()

                    final_state = None

                    for state in run_trip_planner_stepwise(trip_request):
                        current_step = state.get("current_step", "")

                        if current_step == "check_weather":
                            progress_placeholder.progress(20)
                            status_placeholder.info("☁️ Checking weather...")
                            time.sleep(0.5)

                        elif current_step == "search_flights":
                            progress_placeholder.progress(40)
                            status_placeholder.info("✈️ Searching flights...")
                            time.sleep(0.5)

                        elif current_step == "search_hotels":
                            progress_placeholder.progress(60)
                            status_placeholder.info("🏨 Finding hotels...")
                            time.sleep(0.5)

                        elif current_step == "search_attractions":
                            progress_placeholder.progress(80)
                            status_placeholder.info("🎯 Discovering attractions...")
                            time.sleep(0.5)

                        elif current_step == "generate_itinerary":
                            progress_placeholder.progress(95)
                            status_placeholder.info("📋 Generating itinerary...")
                            time.sleep(0.5)

                        final_state = state

                    progress_placeholder.progress(100)
                    status_placeholder.success("✅ Complete!")
                    time.sleep(1)

                    progress_placeholder.empty()
                    status_placeholder.empty()

                    if Config.LANGSMITH_API_KEY:
                        monitor.track_planning_session(trip_request.model_dump(), final_state)

                    st.session_state.final_state = final_state
                    st.session_state.trip_planned = True
                    st.session_state.planning_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "destination": trip_data["destination"]
                    })

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.exception(e)

    else:
        if st.session_state.final_state:
            final_state = st.session_state.final_state

            st.markdown("## 📊 Your Trip Plan")

            # Weather
            if "weather_data" in final_state and final_state["weather_data"]:
                display_weather_step(final_state["weather_data"])
                st.markdown("<br>", unsafe_allow_html=True)

            # Flights
            st.markdown("""
                <div style='background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%); 
                            padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
                    <h3 style='color: white; margin: 0;'>✈️ Flight Options</h3>
                </div>
            """, unsafe_allow_html=True)

            if "flights" in final_state and final_state["flights"]:
                for idx, flight in enumerate(final_state["flights"][:3], 1):
                    display_flight_card(flight, idx)

                st.success("✅ Flights found within budget!")

            st.markdown("<br>", unsafe_allow_html=True)

            # Itinerary
            if "itinerary" in final_state and final_state["itinerary"]:
                itinerary = final_state["itinerary"]

                # Hotels
                if "hotels" in final_state and final_state["hotels"]:
                    display_hotels_section(final_state["hotels"], itinerary)

                # Attractions
                if "attractions" in final_state and final_state["attractions"]:
                    display_attractions_section(final_state["attractions"])
                    
                # Budget Breakdown
                display_budget_breakdown(itinerary, final_state["hotels"], final_state["flights"], final_state["attractions"])


                # Daily Itinerary
                display_itinerary_section(itinerary)

                st.success("✅ **Your complete trip itinerary is ready!**")

            # Buttons
            st.divider()
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔄 Plan New Trip", use_container_width=True):
                    st.session_state.trip_planned = False
                    st.session_state.final_state = None
                    st.rerun()
            with col2:
                if st.button("✏️ Modify Trip", use_container_width=True):
                    st.session_state.trip_planned = False
                    st.rerun()


if __name__ == "__main__":
    main()