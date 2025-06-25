import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
import matplotlib

ENGINE_LOG_PATH = "engine_log.csv"
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


# Utility function to load engine log data
def load_data(path):
    if os.path.exists(path):
        return pd.read_csv(path, parse_dates=["Date"], dayfirst=True)
    return pd.DataFrame()

# Append a new row to the engine log file
def append_engine_log(new_row):
    df = load_data(ENGINE_LOG_PATH)
    updated = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    updated.to_csv(ENGINE_LOG_PATH, index=False)

# Load engine log data
df = load_data(ENGINE_LOG_PATH)

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
    engine_log_columns = load_data(ENGINE_LOG_PATH).columns.tolist()

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

        # Move these inputs OUTSIDE the form so we can check date before rendering the form
    date = st.date_input("Date")
    vessel = st.selectbox("Select Vessel", vessel_list)

    with st.form("engine_log_form"):
            form_data = {"Date": date, "Vessel": vessel}

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

            # This works because 'date' is defined before form
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
                form_data["1ST OF MONTH ME RUNNING HOURS"] = ""
                form_data["1ST OF MONTH AE1 RUNNING HOURS"] = ""
                form_data["1ST OF MONTH AE2 RUNNING HOURS"] = ""
                form_data["1ST OF MONTH AE3 RUNNING HOURS"] = ""
                form_data["1ST OF MONTH ROB HFO"] = ""
                form_data["1ST OF MONTH ROB MDO"] = ""
                form_data["1ST OF MONTH ME CYL OIL"] = ""
                form_data["1ST OF MONTH AE SUMP OIL"] = ""

            with st.expander("Remarks"):
                form_data["Remarks"] = st.text_area("Remarks")

            if st.form_submit_button("Submit Entry"):
                append_engine_log(form_data)
                st.success("Log saved!")
                st.experimental_rerun()

# ---------------- TAB 2: Dashboard ----------------
with tab2:
    st.header("📊 Engine Log Dashboard")
    if df.empty:
        st.warning("No engine log data available.")
    else:
        df = df[df["Date"].notna()]
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month

        vessels = df["Vessel"].dropna().unique()
        selected_vessel = st.selectbox("Select Vessel", sorted(vessels))

        selected_year = st.selectbox("Select Year", sorted(df['Year'].unique()))
        month_names = {1: "January", 2: "February", 3: "March", 4: "April",
                       5: "May", 6: "June", 7: "July", 8: "August",
                       9: "September", 10: "October", 11: "November", 12: "December"}
        selected_month = st.selectbox("Select Month", [month_names[m] for m in sorted(df[df['Year'] == selected_year]['Month'].unique())])
        selected_month_num = {v: k for k, v in month_names.items()}[selected_month]

        filtered = df[(df['Vessel'] == selected_vessel) & (df['Year'] == selected_year) & (df['Month'] == selected_month_num)]

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

            display_cols = {
                "🌡️ Main Engine Temperatures": [
                    "SCAV AIR TEMPERATURE", "HIGHEST EXHAUST GAS TEMPERATURE", "EXHAUST BEFORE T/C TEMPERATURE",
                    "PISTON COOLANT OUTLET TEMPERATURE", "CYL COOLANT OUTLET TEMPERATURE", "LO INLET MAIN ENGINE TEMPERATURE",
                    "STENTUBE BEARING FORE TEMPERATURE", "STERNTUBE BEARING AFT TEMPERATURE", "FUEL INLET TEMPERATURE"
                ],
                "⚙️ Main Engine Pressures": [
                    "SCAV AIR PRESSURE ", "PISTON COOLANT PRESSURE", "CYLINDER COOLANT PRESSURE",
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

            selected_cols = [col for col in display_cols[view_option] if col in filtered.columns]
            display_df = filtered[['Date'] + selected_cols].sort_values("Date")

            # Average row
            avg_row = {col: filtered[col].mean() if pd.api.types.is_numeric_dtype(filtered[col]) else "" for col in selected_cols}
            avg_row["Date"] = "Average"
            avg_df = pd.concat([display_df, pd.DataFrame([avg_row])], ignore_index=True)

            # Render table
            st.markdown("<style>thead th {font-size: 10px !important; white-space: normal !important; word-wrap: break-word !important;} tbody td {font-size: 12px !important;}</style>", unsafe_allow_html=True)
            st.dataframe(avg_df, use_container_width=True, height=500)

            # Optional plot: ME CONSUMPTION HFO AT SEA
            if view_option == "⛽ Fuel Consumption" and "ME CONSUMPTION HFO AT SEA" in filtered.columns:
                st.markdown("### 📈 ME Consumption HFO at Sea - Trend")
                plot_df = filtered[["Date", "ME CONSUMPTION HFO AT SEA"]].dropna().sort_values("Date")

                if not plot_df.empty:
                    import matplotlib.pyplot as plt
                    import matplotlib.dates as mdates

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
