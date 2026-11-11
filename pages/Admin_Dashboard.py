
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from email_sender import send_emergency_alert_email
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

from weather_forecast import get_rainfall_forecast
from datetime import datetime
import uuid




# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="HazardSync | Admin Dashboard",
    page_icon="🌧️",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent.parent

RAINFALL_FILE = BASE_DIR / "kannur_rainfall.csv"
HOSPITAL_FILE = BASE_DIR / "hospitals.csv"
SHELTER_FILE = BASE_DIR / "shelters.csv"
ALERT_FILE = BASE_DIR / "alerts.csv"

ALERT_COLUMNS = [
    "Alert ID",
    "Created At",
    "Forecast Date",
    "Expected Rainfall (mm)",
    "Threshold (mm)",
    "Message",
    "Status"
]

DEFAULT_THRESHOLD = 64.5


# --------------------------------------------------
# CUSTOM DESIGN
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background-color: #0b1120;
    color: #e2e8f0;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
}

h1, h2, h3 {
    color: #e2e8f0;
}

div.stButton > button {
    border-radius: 9px;
    min-height: 45px;
    font-weight: 600;
}

div[data-testid="stMetric"] {
    background-color: #172033;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #263449;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# DATA FUNCTIONS
# --------------------------------------------------

def load_csv(file_path):

    try:
        if file_path.exists():
            return pd.read_csv(file_path)

    except Exception as error:
        st.error(f"Could not read {file_path.name}: {error}")

    return pd.DataFrame()


def load_shelters():

    columns = [
        "Shelter Name",
        "Location",
        "Latitude",
        "Longitude"
    ]

    if SHELTER_FILE.exists():

        try:
            data = pd.read_csv(SHELTER_FILE)

            for column in columns:
                if column not in data.columns:
                    data[column] = ""

            data = data[columns]

            data["Shelter Name"] = (
                data["Shelter Name"]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            data = data[data["Shelter Name"] != ""]

            return data.reset_index(drop=True)

        except Exception as error:
            st.error(f"Unable to load shelters: {error}")

    return pd.DataFrame(columns=columns)


def save_shelters(data):

    data = data.copy()

    data["Shelter Name"] = (
        data["Shelter Name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    data = data[data["Shelter Name"] != ""]

    data.to_csv(SHELTER_FILE, index=False)


def load_alerts():

    if ALERT_FILE.exists():

        try:
            data = pd.read_csv(ALERT_FILE)

            for column in ALERT_COLUMNS:
                if column not in data.columns:
                    data[column] = ""

            data = data[ALERT_COLUMNS]

            data["Status"] = (
                data["Status"]
                .fillna("Active")
                .astype(str)
            )

            return data

        except Exception as error:
            st.error(f"Unable to load alerts: {error}")

    return pd.DataFrame(columns=ALERT_COLUMNS)


def save_alerts(data):

    data.to_csv(ALERT_FILE, index=False)


def get_rainfall_column(data):

    for column in [
        "Daily Actual",
        "Rainfall",
        "Actual Rainfall"
    ]:
        if column in data.columns:
            return column

    return None


def navigate_to(section):

    st.session_state.admin_section = section


def get_forecast():

    try:
        forecast = get_rainfall_forecast()

        if forecast is not None and not forecast.empty:
            return forecast.copy()

    except Exception as error:
        st.error(f"Unable to retrieve rainfall forecast: {error}")

    return pd.DataFrame()


def get_critical_forecast(forecast, threshold):

    if forecast.empty:
        return pd.DataFrame()

    required = ["Date", "Rainfall_mm"]

    if not all(column in forecast.columns for column in required):
        return pd.DataFrame()

    data = forecast.copy()

    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce"
    )

    data["Rainfall_mm"] = pd.to_numeric(
        data["Rainfall_mm"],
        errors="coerce"
    )

    data = data.dropna(
        subset=["Date", "Rainfall_mm"]
    )

    today = pd.Timestamp.now(
        tz="Asia/Kolkata"
    ).date()

    data["Days Ahead"] = data["Date"].apply(
        lambda date: (date.date() - today).days
    )

    data = data[
        data["Days Ahead"].isin([3, 4])
    ]

    data = data[
        data["Rainfall_mm"] >= threshold
    ]

    return data.sort_values("Date")


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:

    st.title("🌧️ HazardSync")
    st.subheader("Administrator Login")

    st.write(
        "Sign in to access the HazardSync administration dashboard."
    )

    with st.form("admin_login_form"):

        username = st.text_input("Username")
        password = st.text_input(
            "Password",
            type="password"
        )

        login_button = st.form_submit_button(
            "Login",
            use_container_width=True
        )

    if login_button:

        if (
                username == st.secrets["admin"]["username"]
                and password == st.secrets["admin"]["password"]
        ):

            st.session_state.admin_logged_in = True
            st.session_state.admin_section = "Admin Overview"

            st.rerun()

        else:
            st.error("Invalid username or password.")

    st.stop()


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

sections = [
    "Admin Overview",
    "Rainfall Alert Management",
    "Infrastructure Management",
    "Preparedness & Recommendations"
]

if "admin_section" not in st.session_state:
    st.session_state.admin_section = "Admin Overview"

st.sidebar.title("🌧️ HazardSync")
st.sidebar.caption("Administrator Portal")

st.sidebar.radio(
    "Navigation",
    sections,
    key="admin_section"
)

st.sidebar.divider()

st.sidebar.button(
    "Logout",
    use_container_width=True,
    on_click=lambda: st.session_state.update({
        "admin_logged_in": False
    })
)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

rainfall_data = load_csv(RAINFALL_FILE)
hospital_data = load_csv(HOSPITAL_FILE)
shelter_data = load_shelters()
alert_data = load_alerts()


# --------------------------------------------------
# ADMIN OVERVIEW
# --------------------------------------------------


if st.session_state.admin_section == "Admin Overview":

    st.title("Admin Dashboard")

    st.write(
        "Monitor rainfall conditions, emergency alerts "
        "and critical infrastructure."
    )

    # LOAD ALERT DATA

    alert_data = load_alerts()

    active_alerts = alert_data[
        alert_data["Status"].astype(str).str.lower() == "active"
    ]

    resolved_alerts = alert_data[
        alert_data["Status"].astype(str).str.lower() == "resolved"
    ]

    # SYSTEM OVERVIEW

    st.subheader("System Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Rainfall Records",
        len(rainfall_data)
    )

    col2.metric(
        "Registered Hospitals",
        len(hospital_data)
    )

    col3.metric(
        "Emergency Shelters",
        len(shelter_data)
    )

    col4.metric(
        "Active Alerts",
        len(active_alerts)
    )

    st.divider()

    # ALERT SUMMARY

    st.subheader("🚨 Alert Summary")

    high_priority_count = active_alerts[
        active_alerts["Message"].astype(str).str.contains(
            "Priority: High",
            case=False,
            na=False
        )
    ].shape[0]

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "Active Alerts",
        len(active_alerts)
    )

    metric2.metric(
        "Resolved Alerts",
        len(resolved_alerts)
    )

    metric3.metric(
        "High-Priority Alerts",
        high_priority_count
    )

    st.divider()

    # EMERGENCY ALERT STATUS

    st.subheader("Emergency Alert Status")

    if not active_alerts.empty:

        st.error(
            f"{len(active_alerts)} active emergency alert(s) "
            "are currently published."
        )

        st.dataframe(
            active_alerts[
                [
                    "Forecast Date",
                    "Expected Rainfall (mm)",
                    "Message",
                    "Status"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success("There are no active published alerts.")

    st.divider()

    # QUICK ACCESS

    st.subheader("Quick Access")

    col1, col2 = st.columns(2)

    with col1:

        st.button(
            "Rainfall Alerts →",
            use_container_width=True,
            on_click=navigate_to,
            args=("Rainfall Alert Management",)
        )

    with col2:

        st.button(
            "Manage Infrastructure →",
            use_container_width=True,
            on_click=navigate_to,
            args=("Infrastructure Management",)
        )

    st.divider()

    # EMERGENCY RESOURCE OVERVIEW

    st.subheader("Emergency Resource Overview")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 🏥 Hospital Directory")

        st.write(
            f"**{len(hospital_data)}** registered hospital records."
        )

        st.button(
            "View Hospitals",
            key="overview_hospitals",
            use_container_width=True,
            on_click=navigate_to,
            args=("Infrastructure Management",)
        )

    with col2:

        st.markdown("### 🏠 Emergency Shelters")

        st.write(
            f"**{len(shelter_data)}** registered emergency shelters."
        )

        st.button(
            "Manage Shelters",
            key="overview_shelters",
            use_container_width=True,
            on_click=navigate_to,
            args=("Infrastructure Management",)
        )


# --------------------------------------------------
# RAINFALL ALERT MANAGEMENT
# --------------------------------------------------


elif st.session_state.admin_section == "Rainfall Alert Management":

    st.title("🌧️ Rainfall Alert Management")

    st.write(
        "Monitor forecast rainfall and publish preparedness alerts "
        "for upcoming heavy rainfall."
    )

    st.divider()

    # AUTOMATIC RAINFALL ALERT SETTINGS

    st.subheader("Forecast Alert Settings")

    threshold = st.number_input(
        "Heavy Rainfall Screening Threshold (mm/day)",
        min_value=1.0,
        max_value=300.0,
        value=DEFAULT_THRESHOLD,
        step=0.5
    )

    st.caption(
        "64.5 mm/day is used as the default heavy-rainfall threshold. "
        "You can adjust it for preparedness screening."
    )

    if st.button(
        "Check Upcoming Rainfall",
        use_container_width=True
    ):

        st.session_state.checked_forecast = True
        st.session_state.forecast_threshold = threshold
        st.session_state.forecast_data = get_forecast()

    if (
        "checked_forecast" in st.session_state
        and st.session_state.checked_forecast
    ):

        forecast = st.session_state.get(
            "forecast_data",
            pd.DataFrame()
        )

        current_threshold = st.session_state.get(
            "forecast_threshold",
            DEFAULT_THRESHOLD
        )

        if forecast.empty:

            st.warning(
                "Unable to retrieve forecast data. "
                "Check your internet connection."
            )

        else:

            st.subheader("3–4 Day Rainfall Forecast")

            forecast_dates = forecast.copy()

            forecast_dates["Date"] = pd.to_datetime(
                forecast_dates["Date"],
                errors="coerce"
            )

            forecast_dates["Rainfall_mm"] = pd.to_numeric(
                forecast_dates["Rainfall_mm"],
                errors="coerce"
            )

            today = pd.Timestamp.now(
                tz="Asia/Kolkata"
            ).date()

            forecast_dates["Days Ahead"] = forecast_dates[
                "Date"
            ].apply(
                lambda date: (
                    (date.date() - today).days
                    if pd.notna(date)
                    else None
                )
            )

            relevant = forecast_dates[
                forecast_dates["Days Ahead"].isin([3, 4])
            ]

            if not relevant.empty:

                st.dataframe(
                    relevant[
                        ["Date", "Days Ahead", "Rainfall_mm"]
                    ].rename(
                        columns={
                            "Date": "Forecast Date",
                            "Days Ahead": "Days Ahead",
                            "Rainfall_mm": "Expected Rainfall (mm)"
                        }
                    ),
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.warning(
                    "The forecast does not contain valid data "
                    "for the 3rd and 4th days ahead."
                )

            critical = get_critical_forecast(
                forecast,
                current_threshold
            )

            st.divider()

            st.subheader("Heavy Rainfall Screening Results")

            if not critical.empty:

                st.warning(
                    "Potential heavy rainfall detected on one or more "
                    "forecast days."
                )

                st.dataframe(
                    critical[
                        ["Date", "Days Ahead", "Rainfall_mm"]
                    ].rename(
                        columns={
                            "Date": "Forecast Date",
                            "Rainfall_mm": "Expected Rainfall (mm)"
                        }
                    ),
                    use_container_width=True,
                    hide_index=True
                )

                st.markdown("### Publish Automatic Rainfall Alert")

                alert_message = st.text_area(
                    "Alert Message",
                    value=(
                        "Heavy rainfall is forecast for the Kannur area. "
                        "Residents should monitor weather updates, "
                        "avoid unnecessary travel through waterlogged "
                        "areas and follow instructions from local authorities."
                    )
                )

                if st.button(
                    "🚨 Send Alert to User Dashboard",
                    type="primary",
                    use_container_width=True
                ):

                    if not alert_message.strip():

                        st.warning("Please enter an alert message.")

                    else:

                        latest_alerts = load_alerts()

                        new_records = []

                        for _, row in critical.iterrows():

                            new_records.append({
                                "Alert ID": str(uuid.uuid4()),
                                "Created At": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "Forecast Date": row["Date"].strftime(
                                    "%Y-%m-%d"
                                ),
                                "Expected Rainfall (mm)": round(
                                    float(row["Rainfall_mm"]), 2
                                ),
                                "Threshold (mm)": current_threshold,
                                "Message": alert_message.strip(),
                                "Status": "Active"
                            })

                        updated_alerts = pd.concat(
                            [
                                latest_alerts,
                                pd.DataFrame(new_records)
                            ],
                            ignore_index=True
                        )

                        save_alerts(updated_alerts)

                        st.success(
                            "Alert published successfully!"
                        )

                        st.rerun()

            else:

                st.success(
                    "No forecast day within the 3–4 day screening window "
                    "has reached the selected rainfall threshold."
                )

    # MANUAL EMERGENCY ALERT

    st.divider()

    st.subheader("🚨 Publish Manual Emergency Alert")

    with st.form("manual_alert_form"):

        manual_title = st.text_input(
            "Alert Title",
            placeholder="Example: Road Flooding Alert"
        )

        manual_area = st.text_input(
            "Affected Area",
            placeholder="Example: Kannur Town"
        )

        manual_type = st.selectbox(
            "Emergency Type",
            [
                "Flood",
                "Landslide",
                "Road Blockage",
                "Heavy Rainfall",
                "Other"
            ]
        )

        manual_priority = st.selectbox(
            "Alert Priority",
            ["High", "Medium", "Low"]
        )

        manual_message = st.text_area(
            "Emergency Instructions",
            placeholder="Enter emergency instructions for residents..."
        )

        publish_manual = st.form_submit_button(
            "🚨 Publish Manual Alert",
            use_container_width=True
        )

    if publish_manual:

        if (
            not manual_title.strip()
            or not manual_area.strip()
            or not manual_message.strip()
        ):

            st.warning("Please fill in all alert details.")

        else:

            latest_alerts = load_alerts()

            new_alert = pd.DataFrame([{
                "Alert ID": str(uuid.uuid4()),
                "Created At": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "Forecast Date": "Manual Alert",
                "Expected Rainfall (mm)": 0,
                "Threshold (mm)": 0,
                "Message": (
                    f"Title: {manual_title.strip()}\n"
                    f"Area: {manual_area.strip()}\n"
                    f"Type: {manual_type}\n"
                    f"Priority: {manual_priority}\n"
                    f"Instructions: {manual_message.strip()}"
                ),
                "Status": "Active"
            }])

            updated_alerts = pd.concat(
                [latest_alerts, new_alert],
                ignore_index=True
            )

            save_alerts(updated_alerts)

            save_alerts(updated_alerts)

            st.success(
                "Manual emergency alert published successfully!"
            )

            # SEND EMAIL NOTIFICATIONS
            email_success, email_message = send_emergency_alert_email(
                manual_title.strip(),
                manual_area.strip(),
                manual_type,
                manual_priority,
                manual_message.strip()
            )

            if email_success:
                st.success(email_message)
            else:
                st.warning(
                    f"Alert published, but email notification was not sent: {email_message}"
                )

            st.rerun()

    # ACTIVE ALERTS

    st.divider()

    st.subheader("Active Alerts")

    alert_data = load_alerts()

    active_alerts = alert_data[
        alert_data["Status"].astype(str).str.lower() == "active"
    ]

    if not active_alerts.empty:

        st.dataframe(
            active_alerts,
            use_container_width=True,
            hide_index=True
        )

        alert_ids = active_alerts["Alert ID"].tolist()

        selected_alert = st.selectbox(
            "Select an alert to resolve",
            alert_ids
        )

        if st.button(
            "Mark Selected Alert as Resolved",
            use_container_width=True
        ):

            alert_data.loc[
                alert_data["Alert ID"] == selected_alert,
                "Status"
            ] = "Resolved"

            save_alerts(alert_data)

            st.success("Alert marked as resolved.")

            st.rerun()

    else:

        st.info("There are no active alerts.")

    # ALERT HISTORY

    st.divider()

    st.subheader("Recent Alert History")

    if not alert_data.empty:

        st.dataframe(
            alert_data.sort_values(
                "Created At",
                ascending=False
            ).head(20),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No alert history is available yet.")

# --------------------------------------------------
# RISK ASSESSMENT MANAGEMENT
# --------------------------------------------------



# --------------------------------------------------
# INFRASTRUCTURE MANAGEMENT
# --------------------------------------------------


elif st.session_state.admin_section == "Infrastructure Management":

    st.title("Infrastructure Management")

    st.write(
        "Manage critical infrastructure and emergency shelters."
    )

    # -------------------------------
    # HOSPITAL DIRECTORY
    # -------------------------------

    st.subheader("Hospital Directory")

    hospital_data = load_csv(HOSPITAL_FILE)

    if not hospital_data.empty:

        st.dataframe(
            hospital_data,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning("No hospital records found.")

    st.divider()

    # -------------------------------
    # ADD HOSPITAL
    # -------------------------------

    st.subheader("Add Hospital")

    with st.form("add_hospital_form"):

        hospital_name = st.text_input("Hospital Name")

        col1, col2 = st.columns(2)

        with col1:

            hospital_latitude = st.number_input(
                "Hospital Latitude",
                format="%.6f",
                key="hospital_latitude"
            )

        with col2:

            hospital_longitude = st.number_input(
                "Hospital Longitude",
                format="%.6f",
                key="hospital_longitude"
            )

        add_hospital_button = st.form_submit_button(
            "Add Hospital"
        )

    if add_hospital_button:

        if not hospital_name.strip():

            st.warning("Please enter the hospital name.")

        elif not (
            -90 <= hospital_latitude <= 90
            and -180 <= hospital_longitude <= 180
        ):

            st.warning("Please enter valid coordinates.")

        else:

            current_hospitals = load_csv(HOSPITAL_FILE)

            new_hospital = pd.DataFrame([{
                "name": hospital_name.strip(),
                "latitude": hospital_latitude,
                "longitude": hospital_longitude
            }])

            updated_hospitals = pd.concat(
                [current_hospitals, new_hospital],
                ignore_index=True
            )

            updated_hospitals.to_csv(
                HOSPITAL_FILE,
                index=False
            )

            st.success("Hospital added successfully!")

            st.rerun()


    st.divider()

    # -------------------------------
    # EDIT AND DELETE HOSPITAL
    # -------------------------------

    st.subheader("Manage Hospitals")

    current_hospitals = load_csv(HOSPITAL_FILE)

    if not current_hospitals.empty:

        hospital_indices = current_hospitals.index.tolist()

        hospital_options = [
            f"{current_hospitals.loc[i, 'name']} (ID: {i})"
            for i in hospital_indices
        ]

        selected_hospital = st.selectbox(
            "Select Hospital",
            hospital_options,
            key="manage_hospital_select"
        )

        selected_index = hospital_indices[
            hospital_options.index(selected_hospital)
        ]

        selected_data = current_hospitals.loc[selected_index]

        st.write("### Edit Hospital Details")

        with st.form("edit_hospital_form"):

            edit_name = st.text_input(
                "Hospital Name",
                value=str(selected_data["name"])
            )

            col1, col2 = st.columns(2)

            with col1:
                edit_latitude = st.number_input(
                    "Latitude",
                    value=float(selected_data["latitude"]),
                    format="%.6f",
                    key="edit_hospital_lat"
                )

            with col2:
                edit_longitude = st.number_input(
                    "Longitude",
                    value=float(selected_data["longitude"]),
                    format="%.6f",
                    key="edit_hospital_lon"
                )

            update_hospital = st.form_submit_button(
                "Update Hospital"
            )

        if update_hospital:

            if not edit_name.strip():

                st.warning("Please enter the hospital name.")

            elif not (
                -90 <= edit_latitude <= 90
                and -180 <= edit_longitude <= 180
            ):

                st.warning("Please enter valid coordinates.")

            else:

                current_hospitals.loc[selected_index, "name"] = edit_name.strip()
                current_hospitals.loc[selected_index, "latitude"] = edit_latitude
                current_hospitals.loc[selected_index, "longitude"] = edit_longitude

                current_hospitals.to_csv(
                    HOSPITAL_FILE,
                    index=False
                )

                st.success("Hospital updated successfully!")

                st.rerun()

        st.divider()

        st.write("### Delete Hospital")

        confirm_hospital_delete = st.checkbox(
            "I confirm that I want to delete this hospital.",
            key="confirm_hospital_delete"
        )

        if st.button("Delete Selected Hospital"):

            if confirm_hospital_delete:

                updated_hospitals = current_hospitals.drop(
                    index=selected_index
                )

                updated_hospitals.to_csv(
                    HOSPITAL_FILE,
                    index=False
                )

                st.success("Hospital deleted successfully!")

                st.rerun()

            else:

                st.warning(
                    "Please confirm before deleting."
                )

    else:

        st.warning("No hospitals available to manage.")


    # -------------------------------
    # ADD EMERGENCY SHELTER
    # -------------------------------

    st.subheader("Add Emergency Shelter")

    with st.form("add_shelter_form"):

        shelter_name = st.text_input("Shelter Name")

        location = st.text_input("Location")

        col1, col2 = st.columns(2)

        with col1:

            latitude = st.number_input(
                "Latitude",
                format="%.6f"
            )

        with col2:

            longitude = st.number_input(
                "Longitude",
                format="%.6f"
            )

        add_button = st.form_submit_button("Add Shelter")

    if add_button:

        if not shelter_name.strip() or not location.strip():

            st.warning(
                "Please enter the shelter name and location."
            )

        elif not (
            -90 <= latitude <= 90
            and -180 <= longitude <= 180
        ):

            st.warning("Please enter valid coordinates.")

        else:

            new_shelter = pd.DataFrame([{
                "Shelter Name": shelter_name.strip(),
                "Location": location.strip(),
                "Latitude": latitude,
                "Longitude": longitude
            }])

            updated_shelters = pd.concat(
                [
                    load_shelters(),
                    new_shelter
                ],
                ignore_index=True
            )

            save_shelters(updated_shelters)

            st.success("Shelter added successfully.")

            st.rerun()

    st.divider()

    # -------------------------------
    # EMERGENCY SHELTER DIRECTORY
    # -------------------------------

    st.subheader("Emergency Shelter Directory")

    current_shelters = load_shelters()

    if not current_shelters.empty:

        st.dataframe(
            current_shelters,
            use_container_width=True,
            hide_index=True
        )

        shelter_options = current_shelters[
            "Shelter Name"
        ].tolist()

        shelter_to_delete = st.selectbox(
            "Select a shelter to delete",
            shelter_options
        )

        confirm_delete = st.checkbox(
            "I confirm that I want to delete this shelter."
        )

        if st.button("Delete Selected Shelter"):

            if confirm_delete:

                updated_shelters = current_shelters[
                    current_shelters["Shelter Name"]
                    != shelter_to_delete
                ]

                save_shelters(updated_shelters)

                st.success("Shelter deleted successfully.")

                st.rerun()

            else:

                st.warning(
                    "Please confirm before deleting."
                )

    else:

        st.warning("No emergency shelters found.")


# --------------------------------------------------
# SCENARIO ANALYSIS
# --------------------------------------------------

# --------------------------------------------------
# PREPAREDNESS & RECOMMENDATIONS
# --------------------------------------------------

elif st.session_state.admin_section == "Preparedness & Recommendations":

    st.title("Preparedness & Recommendations")

    st.write(
        "Review essential preparedness activities."
    )

    st.subheader("Preparedness Checklist")

    st.write(
        "Select the activities that have been completed."
    )

    checklist = [
        "Review emergency shelter availability",
        "Verify hospital and emergency contact details",
        "Check road accessibility",
        "Review evacuation routes",
        "Monitor rainfall observations",
        "Coordinate with local response teams",
        "Check backup power arrangements",
        "Prepare emergency communication plans"
    ]

    completed = 0

    for item in checklist:

        if st.checkbox(
            item,
            key=f"preparedness_{item}"
        ):

            completed += 1

    st.divider()

    st.subheader("Preparedness Progress")

    progress = completed / len(checklist)

    st.progress(progress)

    st.write(
        f"**{completed} of {len(checklist)} activities completed**"
    )

    if completed == len(checklist):

        st.success(
            "All checklist activities have been marked complete."
        )

    else:

        st.info(
            "Continue reviewing the remaining preparedness activities."
        )
