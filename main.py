
from weather_forecast import get_rainfall_forecast
import pandas as pd
import streamlit as st
import folium
import csv
from pathlib import Path
from urllib.parse import quote
from streamlit_folium import st_folium
from email_notifications import register_email

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="HazardSync | Disaster Preparedness",
    page_icon="🌍",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
RAINFALL_FILE = BASE_DIR / "kannur_rainfall.csv"
HOSPITAL_FILE = BASE_DIR / "hospitals.csv"
SHELTER_FILE = BASE_DIR / "shelters.csv"
ALERT_FILE = BASE_DIR / "alerts.csv"

# ==========================================
# 2. CUSTOM DESIGN
# ==========================================

st.markdown("""
<style>
.stApp {
    background-color: #0B1120;
    color: #E5E7EB;
}

[data-testid="stSidebar"] {
    background-color: #111827;
}

h1, h2, h3 {
    color: #F8FAFC;
}

p, label, span {
    color: #CBD5E1;
}

[data-testid="stMetric"] {
    background-color: #1E293B;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #334155;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #111827;
    border-radius: 12px;
}

.stButton > button {
    background-color: #2563EB;
    color: white;
    border-radius: 8px;
    border: none;
    min-height: 42px;
}

.stButton > button:hover {
    background-color: #1D4ED8;
    color: white;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 5px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================

st.sidebar.title("🌍 HazardSync")
st.sidebar.caption("Disaster Preparedness Platform")
st.sidebar.divider()


def navigate_to(section):
    st.session_state["page_nav"] = section


page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Dashboard Overview",
        "Rainfall Monitoring",
        "Critical Infrastructure",
        "Scenario Simulator & Recommendations"
    ],
    key="page_nav"
)

st.sidebar.divider()
st.sidebar.caption("Location: Kannur, Kerala")
st.sidebar.caption("Pre-disaster planning prototype")

# ==========================================
# 4. LOAD INFRASTRUCTURE DATA
# ==========================================

def load_hospitals():
    records = []

    if HOSPITAL_FILE.exists():
        try:
            with open(
                HOSPITAL_FILE,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                reader = csv.DictReader(file)

                for row in reader:
                    try:
                        records.append({
                            "name": row["name"],
                            "latitude": float(row["latitude"]),
                            "longitude": float(row["longitude"])
                        })
                    except (KeyError, ValueError, TypeError):
                        continue

        except Exception:
            pass

    return records


hospitals = load_hospitals()


def load_shelters():
    records = []

    if SHELTER_FILE.exists():
        try:
            with open(
                SHELTER_FILE,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                reader = csv.DictReader(file)

                for row in reader:
                    try:
                        name = row.get("Shelter Name", "").strip()
                        address = row.get("Location", "").strip()

                        if not name:
                            continue

                        records.append({
                            "name": name,
                            "address": address,
                            "latitude": float(row["Latitude"]),
                            "longitude": float(row["Longitude"])
                        })

                    except (KeyError, ValueError, TypeError):
                        continue

        except Exception as error:
            st.error(f"Unable to load shelters: {error}")

    return records


shelters = load_shelters()

# ==========================================
# 5. LOAD RAINFALL DATA
# ==========================================

def load_rainfall():
    if not RAINFALL_FILE.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(RAINFALL_FILE)

        required_columns = [
            "Date",
            "Daily Actual",
            "Daily Normal"
        ]

        if not all(column in df.columns for column in required_columns):
            return pd.DataFrame()

        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        )

        df["Daily Actual"] = pd.to_numeric(
            df["Daily Actual"],
            errors="coerce"
        )

        df["Daily Normal"] = pd.to_numeric(
            df["Daily Normal"],
            errors="coerce"
        )

        df = df.dropna(subset=["Date", "Daily Actual"])

        return df.sort_values("Date")

    except Exception:
        return pd.DataFrame()


rainfall_df = load_rainfall()

# ==========================================
# 6. REUSABLE MAP FUNCTION
# ==========================================

def create_infrastructure_map():

    hazard_map = folium.Map(
        location=[11.8745, 75.3704],
        zoom_start=13,
        tiles="OpenStreetMap"
    )

    for hospital in hospitals:

        folium.Marker(
            location=[
                hospital["latitude"],
                hospital["longitude"]
            ],
            popup=hospital["name"],
            tooltip=hospital["name"],
            icon=folium.Icon(
                color="red",
                icon="plus-sign"
            )
        ).add_to(hazard_map)

    for shelter in shelters:

        folium.Marker(
            location=[
                shelter["latitude"],
                shelter["longitude"]
            ],
            popup=shelter["name"] + " - " + shelter["address"],
            tooltip=shelter["name"],
            icon=folium.Icon(
                color="blue",
                icon="home"
            )
        ).add_to(hazard_map)

    return hazard_map


# ==========================================
# 7. HEADER
# ==========================================

st.title("🌍 HazardSync")

st.subheader(
    "Pre-Disaster Risk Assessment & Preparedness"
)

st.write(
    "An integrated platform to examine potential disaster risks, "
    "understand possible cascading impacts and support preparedness "
    "planning for critical infrastructure."
)

st.caption(
    "Planning prototype | Kannur, Kerala"
)

st.divider()


# ==========================================
# 9. EMERGENCY ALERTS
# ==========================================

st.subheader("🚨 Emergency Alerts")

if ALERT_FILE.exists():

    alerts = pd.read_csv(ALERT_FILE)

    if not alerts.empty and "Status" in alerts.columns:

        active_alerts = alerts[
            alerts["Status"].astype(str).str.strip().str.lower()
            == "active"
        ]

        if not active_alerts.empty:

            for _, alert in active_alerts.iterrows():

                message = str(alert.get("Message", ""))

                if message.startswith("Title:"):

                    details = {}

                    for line in message.split("\n"):

                        if ":" in line:
                            key, value = line.split(":", 1)
                            details[key.strip()] = value.strip()

                    priority = details.get("Priority", "Medium")

                    st.error(
                        f"🚨 {details.get('Title', 'Emergency Alert')}\n\n"
                        f"📍 **Affected Area:** "
                        f"{details.get('Area', 'Not specified')}\n\n"
                        f"⚠️ **Type:** {details.get('Type', 'Other')}\n\n"
                        f"**Priority:** {priority}\n\n"
                        f"**Instructions:** "
                        f"{details.get('Instructions', '')}"
                    )

                else:

                    st.error(
                        f"🚨 **Heavy Rainfall Alert**\n\n{message}"
                    )

        else:
            st.success("No active emergency alerts.")

    else:
        st.info("No emergency alerts have been published yet.")

else:
    st.info("No emergency alerts have been published yet.")

st.divider()

# ==========================================
# PAGE 1: DASHBOARD OVERVIEW
# ==========================================

if page == "Dashboard Overview":

    st.header("📊 Dashboard Overview")

    # EMAIL REGISTRATION
    st.subheader("📧 Emergency Email Notifications")

    st.write(
        "Register your email address to receive emergency alerts "
        "from HazardSync."
    )

    with st.form("email_registration_form"):

        user_email = st.text_input(
            "Enter your email address"
        )

        submit_email = st.form_submit_button(
            "Register Email"
        )

        if submit_email:

            success, message = register_email(user_email)

            if success:
                st.success(message)
            else:
                st.warning(message)

    st.divider()

    # Keep your existing Dashboard Overview code below this.

    col1, col2, col3, col4 = st.columns(4)

    if not rainfall_df.empty:

        latest = rainfall_df.iloc[-1]

        col1.metric(
            "Latest Recorded Rainfall",
            f'{latest["Daily Actual"]:.2f}'
        )

        col2.metric(
            "Average Rainfall",
            f'{rainfall_df["Daily Actual"].mean():.2f}'
        )

    else:
        col1.metric("Latest Recorded Rainfall", "N/A")
        col2.metric("Average Rainfall", "N/A")

    col3.metric("Registered Hospitals", len(hospitals))
    col4.metric("Registered Shelters", len(shelters))

    st.divider()

    st.subheader("🛡️ Available Services")

    col1, col2, col3 = st.columns(3)

    with col1:

        with st.container(border=True):

            st.subheader("🌧️ Rainfall Monitoring")

            st.write(
                "View rainfall observations and 7-day weather forecasts."
            )

            st.button(
                "View Rainfall Forecast →",
                key="open_rainfall",
                use_container_width=True,
                on_click=navigate_to,
                args=("Rainfall Monitoring",)
            )

    with col2:

        with st.container(border=True):

            st.subheader("🏥 Critical Infrastructure")

            st.write(
                "View hospitals and registered emergency shelters."
            )

            st.button(
                "Open Infrastructure →",
                key="open_infrastructure",
                use_container_width=True,
                on_click=navigate_to,
                args=("Critical Infrastructure",)
            )

    with col3:

        with st.container(border=True):

            st.subheader("⚠️ Scenario Simulator")

            st.write(
                "Explore possible impacts and recommendations."
            )

            st.button(
                "Open Simulator →",
                key="open_simulator",
                use_container_width=True,
                on_click=navigate_to,
                args=("Scenario Simulator & Recommendations",)
            )


# ==========================================
# PAGE 2: RAINFALL MONITORING
# ==========================================

elif page == "Rainfall Monitoring":

    st.header("🌧️ Rainfall Monitoring")

    st.write(
        "Explore rainfall observations and upcoming "
        "weather forecasts for Kannur."
    )

    if not rainfall_df.empty:

        st.subheader("Recent Rainfall Trend")

        recent = rainfall_df.tail(7)

        st.bar_chart(
            recent.set_index("Date")["Daily Actual"]
        )

        st.subheader("Actual Rainfall vs Normal Rainfall")

        chart_data = rainfall_df.set_index("Date")[
            ["Daily Actual", "Daily Normal"]
        ]

        st.line_chart(chart_data)

        st.caption(
            "Source: IMD district-wise daily rainfall dataset. "
            "These are recorded observations, not forecasts."
        )

    else:

        st.warning(
            "Kannur rainfall data is unavailable. "
            "Check that kannur_rainfall.csv exists."
        )

    st.divider()

    st.subheader("📅 7-Day Rainfall Forecast")

    forecast_df = get_rainfall_forecast()

    if forecast_df is not None and not forecast_df.empty:

        st.caption(
            "Weather forecast provided by Open-Meteo "
            "for the location near Kannur."
        )

        col1, col2 = st.columns(2)

        highest_rain = forecast_df.loc[
            forecast_df["Rainfall_mm"].idxmax()
        ]

        col1.metric(
            "Highest Expected Rainfall",
            f'{highest_rain["Rainfall_mm"]:.2f} mm'
        )

        col2.metric(
            "Highest Rain Probability",
            f'{forecast_df["Rain_Probability_Percent"].max():.0f}%'
        )

        st.subheader("Expected Daily Rainfall")

        st.bar_chart(
            forecast_df.set_index("Date")["Rainfall_mm"]
        )

        st.subheader("Rainfall Probability")

        st.line_chart(
            forecast_df.set_index("Date")[
                "Rain_Probability_Percent"
            ]
        )

        st.subheader("7-Day Forecast Details")

        st.dataframe(
            forecast_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "Unable to retrieve the weather forecast. "
            "Please check your internet connection."
        )


# ==========================================
# PAGE 3: CRITICAL INFRASTRUCTURE
# ==========================================

elif page == "Critical Infrastructure":

    st.header("🏥 Critical Infrastructure")

    st.write(
        "Review the hospital and emergency shelter records "
        "currently registered in HazardSync."
    )

    col1, col2 = st.columns(2)

    col1.metric("Registered Hospitals", len(hospitals))
    col2.metric("Registered Shelters", len(shelters))

    st.divider()

    st.subheader("Hospital Directory")

    if hospitals:

        for index, hospital in enumerate(hospitals):

            with st.container(border=True):

                st.write("🏥 **" + hospital["name"] + "**")

                st.write(
                    "Coordinates:",
                    hospital["latitude"],
                    ",",
                    hospital["longitude"]
                )

                destination = (
                    f'{hospital["latitude"]},'
                    f'{hospital["longitude"]}'
                )

                maps_url = (
                    "https://www.google.com/maps/dir/?api=1"
                    f"&destination={quote(destination)}"
                )

                st.link_button(
                    "Get Directions",
                    maps_url,
                    key="hospital_" + str(index)
                )

    else:
        st.info("No hospitals are registered.")

    st.divider()

    st.subheader("Registered Emergency Shelters")

    if shelters:

        for index, shelter in enumerate(shelters):

            with st.container(border=True):

                st.write("🏠 **" + shelter["name"] + "**")

                st.write("Address:", shelter["address"])

                st.write(
                    "Coordinates:",
                    shelter["latitude"],
                    ",",
                    shelter["longitude"]
                )

                destination = (
                    f'{shelter["latitude"]},'
                    f'{shelter["longitude"]}'
                )

                maps_url = (
                    "https://www.google.com/maps/dir/?api=1"
                    f"&destination={quote(destination)}"
                )

                st.link_button(
                    "Get Directions",
                    maps_url,
                    key="shelter_" + str(index)
                )

    else:
        st.info("No emergency shelters have been registered.")

    st.caption(
        "Only registered records are displayed. "
        "Verify facility details and operational status with authorities."
    )

    st.divider()

    st.subheader("Infrastructure Location Map")

    st_folium(
        create_infrastructure_map(),
        width=None,
        height=450,
        key="infrastructure_map"
    )


# ==========================================
# PAGE 4: SCENARIO SIMULATOR
# ==========================================

elif page == "Scenario Simulator & Recommendations":

    st.header("🌧️ Disaster Scenario Simulator")

    st.write(
        "Select hypothetical conditions to explore possible "
        "cascading impacts and preparedness actions."
    )

    with st.container(border=True):

        st.subheader("Scenario Configuration")

        location = st.text_input(
            "Area to Assess",
            value="Kannur"
        )

        disaster = st.selectbox(
            "Hazard Type",
            ["Flood", "Landslide", "Cyclone"]
        )

        rainfall = st.slider(
            "Assumed Rainfall Intensity (%)",
            0, 100, 50,
            help="A hypothetical scenario input, not a live measurement."
        )

        road = st.selectbox(
            "Assumed Road Condition",
            [
                "Operational",
                "Partially Blocked",
                "Fully Blocked"
            ]
        )

        electricity = st.selectbox(
            "Assumed Electricity Condition",
            ["Operational", "Disrupted"]
        )

    if st.button("Run Risk Simulation", type="primary"):

        if not location.strip():

            st.error("Please enter an area to assess.")

        else:

            impacts = []
            recommendations = []

            # Flood scenario

            if disaster == "Flood" and rainfall >= 70:

                impacts.append(
                    "High-rainfall scenario: low-lying areas may face "
                    "increased waterlogging or flooding risk."
                )

                recommendations.append(
                    "Inspect drainage channels and identify flood-prone locations."
                )

                recommendations.append(
                    "Review the readiness of shelters in potentially affected areas."
                )

            elif disaster == "Flood" and rainfall >= 40:

                impacts.append(
                    "Moderate-rainfall scenario: monitor drainage "
                    "and locations with a history of waterlogging."
                )

                recommendations.append(
                    "Monitor rainfall and water levels in vulnerable locations."
                )

            # Landslide scenario

            if disaster == "Landslide" and rainfall >= 70:

                impacts.append(
                    "Heavy rainfall may increase landslide risk "
                    "in susceptible slopes and hillside areas."
                )

                recommendations.append(
                    "Inspect known landslide-prone slopes and follow "
                    "local authority guidance."
                )

            elif disaster == "Landslide" and rainfall >= 40:

                impacts.append(
                    "Rainfall may increase concern in susceptible slope areas."
                )

                recommendations.append(
                    "Increase monitoring of known vulnerable slopes."
                )

            # Cyclone scenario

            if disaster == "Cyclone":

                impacts.append(
                    "Cyclone conditions may cause strong winds, "
                    "transport disruption and interruptions to public services."
                )

                recommendations.append(
                    "Monitor official weather alerts and emergency instructions."
                )

                recommendations.append(
                    "Check readiness of shelters and essential services."
                )

            # Road condition

            if road == "Partially Blocked":

                impacts.append(
                    "Road access may be reduced in the selected scenario."
                )

                recommendations.append(
                    "Identify alternative routes for emergency vehicles."
                )

            elif road == "Fully Blocked":

                impacts.append(
                    "The selected road route is assumed to be inaccessible."
                )

                recommendations.append(
                    "Identify alternative access routes to hospitals and shelters."
                )

            if road != "Operational":

                impacts.append(
                    "Ambulance access and movement of relief supplies may be affected."
                )

            # Electricity condition

            if electricity == "Disrupted":

                impacts.append(
                    "Electricity-dependent services may experience disruption."
                )

                recommendations.append(
                    "Check backup power readiness at hospitals and essential facilities."
                )

            if not impacts:

                impacts.append(
                    "The selected scenario does not trigger a major impact "
                    "under the current prototype rules."
                )

                recommendations.append(
                    "Continue monitoring official weather and local risk information."
                )

            # Illustrative risk score

            risk_score = 0

            if rainfall >= 70:
                risk_score += 2

            elif rainfall >= 40:
                risk_score += 1

            if road == "Partially Blocked":
                risk_score += 1

            elif road == "Fully Blocked":
                risk_score += 2

            if electricity == "Disrupted":
                risk_score += 1

            if disaster == "Landslide" and rainfall >= 40:
                risk_score += 1

            if disaster == "Cyclone":
                risk_score += 1

            if risk_score >= 4:
                risk_level = "High"

            elif risk_score >= 2:
                risk_level = "Moderate"

            else:
                risk_level = "Low"

            st.divider()

            st.subheader("Selected Planning Scenario")

            col1, col2 = st.columns(2)

            with col1:

                st.write("**Area:**", location)
                st.write("**Hazard:**", disaster)
                st.write("**Assumed rainfall:**", str(rainfall) + "%")

            with col2:

                st.write("**Road condition:**", road)
                st.write("**Electricity:**", electricity)

            st.divider()

            st.subheader("Illustrative Scenario Risk Level")

            if risk_level == "High":
                st.error("HIGH scenario risk")

            elif risk_level == "Moderate":
                st.warning("MODERATE scenario risk")

            else:
                st.success("LOW scenario risk")

            st.caption(
                "Generated using simple demonstration rules. "
                "This is not a calibrated probability or official warning."
            )

            st.divider()

            st.subheader("Possible Cascading Impacts")

            for impact in impacts:
                st.warning(impact)

            st.subheader("Possible Cascading Impact Chain")

            if (
                disaster == "Flood"
                and rainfall >= 70
                and road != "Operational"
            ):

                st.write("🌧️ Heavy rainfall scenario")
                st.write("⬇️ Possible flooding or waterlogging")
                st.write("⬇️ Potential road disruption")
                st.write("⬇️ Reduced emergency vehicle access")
                st.write("⬇️ Possible difficulty reaching hospitals and shelters")

            elif disaster == "Landslide" and rainfall >= 70:

                st.write("🌧️ Heavy rainfall")
                st.write("⬇️ Possible slope instability")
                st.write("⬇️ Potential landslide")
                st.write("⬇️ Possible road blockage")
                st.write("⬇️ Potential disruption to emergency response")

            elif road != "Operational":

                st.write("🚧 Road disruption")
                st.write("⬇️ Reduced emergency vehicle access")
                st.write("⬇️ Possible delays in emergency response")

            elif electricity == "Disrupted":

                st.write("⚡ Electricity disruption")
                st.write("⬇️ Possible interruption to essential services")

            else:

                st.info(
                    "No cascading impact chain was triggered "
                    "by the current demonstration rules."
                )

            st.divider()

            st.subheader("Preventive & Preparedness Recommendations")

            recommendations = list(dict.fromkeys(recommendations))

            for recommendation in recommendations:
                st.write("✓", recommendation)


# ==========================================
# 10. FOOTER
# ==========================================

st.divider()

st.caption(
    "HazardSync | Pre-Disaster Risk Assessment & Preparedness | Kannur"
)
