import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import base64
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Google Sheets credentials and setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(creds)
sheet = client.open("EngineLogSheet").sheet1

# Utility function to load engine log data
def load_data():
    raw_values = sheet.get_all_values()
    if not raw_values:
        return pd.DataFrame()

    headers = raw_values[0]
    clean_headers = [h.strip() for h in headers]
    records = raw_values[1:]
    df = pd.DataFrame(records, columns=clean_headers)

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], format="%Y-%m-%d", errors='coerce')

    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except:
            continue
    return df

def append_engine_log(new_row):
    if 'Date' in new_row:
        try:
            if isinstance(new_row['Date'], str):
                parsed = datetime.strptime(new_row['Date'], "%Y-%m-%d")
            else:
                parsed = new_row['Date']
            new_row['Date'] = parsed.strftime("%Y-%m-%d")  # use ISO format
        except Exception as e:
            print("Date format error:", e)
    sheet.append_row([str(new_row.get(k, "")) for k in new_row])


logo_path = "images/Reederei_Nord_Logo_CMYK_blue_V1.jpg"
st.set_page_config(page_title="Engine Log Dashboard", layout="wide")

st.markdown(
    f"""
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="flex-grow: 1;">
            <h1 style="margin-bottom: 0;">🚢 Engine Log Monitoring System</h1>
        </div>
        <div style="flex-shrink: 0;">
            <img src="data:image/jpeg;base64,{base64.b64encode(open(logo_path, "rb").read()).decode()}" 
                 alt="Reederei Nord Logo" style="height: 60px; margin-left: 20px;" />
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Load engine log data

# ---------------- TAB STRUCTURE ----------------
tab1, tab2 = st.tabs(["📥 Engine Log Entry", "📊 Engine Log Dashboard"])

# ---------------- TAB 1: Data Entry ----------------
with tab1:
    st.header("🔧 Add Engine Log Entry")
    vessel_list = [
        "Nordmarlin", "Norddolphin", "Nordindepndence", "Nordpenguin", "Nordtokyo",
        "Nordorse", "Nordtulip", "Nordlotus", "Nordorchid", "Nordsymphony",
        "Angelic Anna", "Radiant Reb"
    ]

    section_map = {
        "General Info": ["VESSEL POSITION", "TIME SHIFT +/- HOURS", "WIND FORCE BFT", "WIND DIRECTION"],
        "Durations": ["DURATION ANCHORAGE DRIFTING", "DURATION IN PORT"],
        "Distances": ["SEA DISTANCE NM", "MANOEUVRE DISTANCE NM", "TOTAL DISTANCENM", "THEOR AT SEA DISTANCE NM", "NOMINAL SLIP %", "SPEED ACTUAL KN"],
        "Ambient Temperatures": ["AMBIENT SEA WATER TEMP", "AMBIENT OUTSIDE AIR TEMP", "AMBIENT ENGINE ROOM TEMP"],
        "Main Engine Operation": ["PROP RPM AT SEA", "MAIN ENGINE LOAD %", "VESSEL MIDSHIP DRAFT", "ME TIME IN OPERATION, SEA", "ME TIME IN OPERATION, MANOEUVRE", "ME TIME IN OPERATION, CARGO OPERATION", "ME TIME IN OPERATION, TOTAL", "MAIN ENGINE RUNNING HOURS"],
        "Auxiliary Engines": ["AUX ENGINE 1 RUNNING HOURS", "AUX ENGINE 2 RUNNING HOURS", "AUX ENGINE 3 RUNNING HOURS"],
        "Equipment Temperatures": ["SCAV AIR TEMPERATURE", "HIGHEST EXHAUST GAS TEMPERATURE", "EXHAUST BEFORE T/C TEMPERATURE", "PISTON COOLANT OUTLET TEMPERATURE", "CYL COOLANT OUTLET TEMPERATURE", "LO INLET MAIN ENGINE TEMPERATURE", "STENTUBE BEARING FORE TEMPERATURE", "STERNTUBE BEARING AFT TEMPERATURE", "FUEL INLET TEMPERATURE"],
        "Equipment Pressures": ["SCAV AIR PRESSURE ", "PISTON COOLANT PRESSURE", "CYLINDER COOLANT PRESSURE", "LO INLET MAIN ENGINE PRESSURE", "STERNTUBE LO PRESSURE", "STERNTUBE AIR PRESSURE", "FUEL INLET PRESSURE"],
        "Fuel Consumptions": ["ME CONSUMPTION HFO AT SEA", "ME CONSUMPTION HFO MANOEUVRE", "ME CONSUMPTION HFO CARGO OPERATION", "ME CONSUMPTION MDO (MGO)", "AUX ENGINES CONSUMPTION HFO AT SEA", "AUX ENGINE CONSUMPTION HFO MANOEUVRE", "AUX ENGINES CONSUMPTION HFO PORT", "AUX ENGINE CONSUMPTIONS MDO (MGO)", "AUX ENGINES CONSUMPTION GENERATOR LOAD", "BOILERS, IGG CONSUMPTION HFO AT SEA", "BOILERS, IGG CONSUMPTION HFO PORT", "BOILERS, IGG CONSUMPTION MANOEUVRE / ANCHOR DRIFTING", "BOILERS, IGG CONSUMPTION MDO (MGO)"],
        "LO Consumptions": ["MAIN ENGINE SUMP LUBOIL CONSUMPTION ", "MAIN ENGINE CYL OIL LUBOIL CONSUMPTION", "START AIR COMP SUMP LUBOIL CONSUMPTION", "AUX ENGINE 1 LUBOIL CONSUMPTION", "AUX ENGINE 2 LUBOIL CONSUMPTION", "AUX ENGINE 3 LUBOIL CONSUMPTION"],
        "Freshwater & Others": ["STERN TUBE ADD LO ", "FRESH WATER GEN PROD "]
    }

    date = st.date_input("Date")
    vessel = st.selectbox("Select Vessel", vessel_list)
    form_data = {"Date": date.strftime("%Y-%m-%d"), "Vessel": vessel}

    with st.form("engine_log_form"):
        for section, fields in section_map.items():
            with st.expander(section):
                for col in fields:
                    clean_col = col.strip()
                    if any(x in clean_col.upper() for x in ["TEMP", "PRESSURE", "%", "RPM", "LOAD"]):
                        form_data[clean_col] = st.number_input(clean_col, step=0.1)
                    elif any(x in clean_col.upper() for x in ["CONSUMPTION", "DISTANCE", "HOURS"]):
                        form_data[clean_col] = st.number_input(clean_col, step=0.1)
                    elif any(x in clean_col.upper() for x in ["POSITION", "DIRECTION"]):
                        form_data[clean_col] = st.text_input(clean_col)
                    else:
                        form_data[clean_col] = st.text_input(clean_col)

        if date.day == 1:
            st.markdown("### 🔁 1st of Month Running Hours & ROB")
            with st.expander("1st of Month - Running Hours"):
                form_data["1ST OF MONTH ME RUNNING HOURS"] = st.number_input("1st of Month ME Running Hours", step=0.1)
                form_data["1ST OF MONTH AE1 RUNNING HOURS"] = st.number_input("1st of Month AE1 Running Hours", step=0.1)
                form_data["1ST OF MONTH AE2 RUNNING HOURS"] = st.number_input("1st of Month AE2 Running Hours", step=0.1)
                form_data["1ST OF MONTH AE3 RUNNING HOURS"] = st.number_input("1st of Month AE3 Running Hours", step=0.1)

            with st.expander("1st of Month - ROB & Oils"):
                form_data["1ST OF MONTH ROB HFO"] = st.number_input("1st of Month ROB HFO", step=0.1)
                form_data["1ST OF MONTH ROB MDO"] = st.number_input("1st of Month ROB MDO", step=0.1)
                form_data["1ST OF MONTH ME CYL OIL"] = st.number_input("1st of Month ME CYL OIL", step=0.1)
                form_data["1ST OF MONTH AE SUMP OIL"] = st.number_input("1st of Month AE SUMP OIL", step=0.1)
        else:
            for key in [
                "1ST OF MONTH ME RUNNING HOURS", "1ST OF MONTH AE1 RUNNING HOURS", "1ST OF MONTH AE2 RUNNING HOURS",
                "1ST OF MONTH AE3 RUNNING HOURS", "1ST OF MONTH ROB HFO", "1ST OF MONTH ROB MDO",
                "1ST OF MONTH ME CYL OIL", "1ST OF MONTH AE SUMP OIL"]:
                form_data[key] = ""

        with st.expander("Remarks"):
            form_data["Remarks"] = st.text_area("Remarks")

        if st.form_submit_button("Submit Engine Log Entry"):
            append_engine_log(form_data)
            st.success("Engine log entry saved.")
            st.rerun()

# ---------------- TAB 2: Dashboard ----------------
with tab2:
    st.header("📊 Engine Log Dashboard")

    df = load_data()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df[df['Date'].notna()]

    if not df.empty and "Vessel" in df.columns:
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month

        vessels = df["Vessel"].dropna().unique()
        selected_vessel = st.selectbox("Select Vessel", sorted(vessels))

        selected_year = st.selectbox("Select Year", sorted(df['Year'].dropna().unique()))
        month_names = {1: "January", 2: "February", 3: "March", 4: "April",
                       5: "May", 6: "June", 7: "July", 8: "August",
                       9: "September", 10: "October", 11: "November", 12: "December"}

        available_months = df[df['Year'] == selected_year]['Month'].dropna().unique()
        selected_month = st.selectbox(
            "Select Month", [month_names[m] for m in sorted(available_months)]
        )
        selected_month_num = {v: k for k, v in month_names.items()}[selected_month]

        filtered = df[
            (df['Vessel'] == selected_vessel) &
            (df['Year'] == selected_year) &
            (df['Month'] == selected_month_num)
        ]

        if filtered.empty:
            st.warning("No data available for the selected filters.")
        else:
            view_option = st.selectbox("Select Data View", [
                "🌡️ Main Engine Temperatures",
                "⚙️ Main Engine Pressures",
                "⛽ Fuel Consumption",
                "🧭 Vessel Position + Durations",
                "📏 Distances / Ambient Temperature",
                "🛢️ Luboil Consumption + Running Hours"
            ])

            view_column_mappings = {
                "🌡️ Main Engine Temperatures": [
                    "SCAV AIR TEMPERATURE", "HIGHEST EXHAUST GAS TEMPERATURE", "EXHAUST BEFORE T/C TEMPERATURE",
                    "PISTON COOLANT OUTLET TEMPERATURE", "CYL COOLANT OUTLET TEMPERATURE", "LO INLET MAIN ENGINE TEMPERATURE",
                    "STENTUBE BEARING FORE TEMPERATURE", "STERNTUBE BEARING AFT TEMPERATURE", "FUEL INLET TEMPERATURE"
                ],
                "⚙️ Main Engine Pressures": [
                    "SCAV AIR PRESSURE", "PISTON COOLANT PRESSURE", "CYLINDER COOLANT PRESSURE",
                    "LO INLET MAIN ENGINE PRESSURE", "STERNTUBE LO PRESSURE", "STERNTUBE AIR PRESSURE", "FUEL INLET PRESSURE"
                ],
                "⛽ Fuel Consumption": [
                    "ME CONSUMPTION HFO AT SEA", "ME CONSUMPTION HFO MANOEUVRE", "ME CONSUMPTION HFO CARGO OPERATION", "ME CONSUMPTION MDO (MGO)",
                    "AUX ENGINES CONSUMPTION HFO AT SEA", "AUX ENGINE CONSUMPTION HFO MANOEUVRE", "AUX ENGINES CONSUMPTION HFO PORT",
                    "AUX ENGINE CONSUMPTIONS MDO (MGO)", "AUX ENGINES CONSUMPTION GENERATOR LOAD",
                    "BOILERS, IGG CONSUMPTION HFO AT SEA", "BOILERS, IGG CONSUMPTION HFO PORT",
                    "BOILERS, IGG CONSUMPTION MANOEUVRE / ANCHOR DRIFTING", "BOILERS, IGG CONSUMPTION MDO (MGO)"
                ],
                "🧭 Vessel Position + Durations": [
                    "VESSEL POSITION", "TIME SHIFT +/- HOURS", "WIND FORCE BFT", "WIND DIRECTION",
                    "ME TIME IN OPERATION, SEA", "ME TIME IN OPERATION, MANOEUVRE",
                    "ME TIME IN OPERATION, CARGO OPERATION", "ME TIME IN OPERATION, TOTAL",
                    "DURATION ANCHORAGE DRIFTING", "DURATION IN PORT"
                ],
                "📏 Distances / Ambient Temperature": [
                    "SEA DISTANCE NM", "MANOEUVRE DISTANCE NM", "TOTAL DISTANCENM", "THEOR AT SEA DISTANCE NM",
                    "NOMINAL SLIP %", "SPEED ACTUAL KN",
                    "AMBIENT SEA WATER TEMP", "AMBIENT OUTSIDE AIR TEMP", "AMBIENT ENGINE ROOM TEMP",
                    "PROP RPM AT SEA", "MAIN ENGINE LOAD %", "VESSEL MIDSHIP DRAFT"
                ],
                "🛢️ Luboil Consumption + Running Hours": [
                    "MAIN ENGINE CYL OIL LUBOIL CONSUMPTION", "START AIR COMP SUMP LUBOIL CONSUMPTION",
                    "AUX ENGINE 1 LUBOIL CONSUMPTION", "AUX ENGINE 2 LUBOIL CONSUMPTION", "AUX ENGINE 3 LUBOIL CONSUMPTION",
                    "MAIN ENGINE RUNNING HOURS", "AUX ENGINE 1 RUNNING HOURS", "AUX ENGINE 2 RUNNING HOURS",
                    "AUX ENGINE 3 RUNNING HOURS", "STERN TUBE ADD LO", "FRESH WATER GEN PROD"
                ]
            }

            selected_cols = [col for col in view_column_mappings[view_option] if col in filtered.columns]
            display_df = filtered[['Date'] + selected_cols].sort_values("Date")

            avg_row = {col: filtered[col].mean() if pd.api.types.is_numeric_dtype(filtered[col]) else "" for col in selected_cols}
            avg_row["Date"] = "Average"
            avg_df = pd.concat([display_df, pd.DataFrame([avg_row])], ignore_index=True)

            st.markdown("<style>thead th {font-size: 10px !important;} tbody td {font-size: 12px !important;}</style>", unsafe_allow_html=True)
            st.dataframe(avg_df, use_container_width=True, height=500)

            if view_option == "⛽ Fuel Consumption" and "ME CONSUMPTION HFO AT SEA" in filtered.columns:
                st.markdown("### 📈 ME Consumption HFO at Sea - Trend")
                plot_df = filtered[["Date", "ME CONSUMPTION HFO AT SEA"]].dropna().sort_values("Date")
                if not plot_df.empty:
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.plot(plot_df["Date"], plot_df["ME CONSUMPTION HFO AT SEA"], marker='o')
                    ax.set_title("ME Consumption HFO at Sea")
                    ax.set_xlabel("Date")
                    ax.set_ylabel("HFO Consumption")
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))
                    ax.grid(True)
                    st.pyplot(fig)
                else:
                    st.info("No data available for plotting.")
    else:
        st.warning("No valid data found in engine log file.")
