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
    headers = sheet.row_values(1)  # Get the header row from the sheet
    row = []

    for col in headers:
        value = new_row.get(col.strip(), "")  # Match form input by header name
        if isinstance(value, float) and pd.isna(value):  # Handle NaNs
            value = ""
        row.append(str(value))

    # Format date properly
    if 'Date' in new_row:
        try:
            if isinstance(new_row['Date'], str):
                parsed = datetime.strptime(new_row['Date'], "%Y-%m-%d")
            else:
                parsed = new_row['Date']
            row[headers.index('Date')] = parsed.strftime("%Y-%m-%d")
        except Exception as e:
            print("Date format error:", e)

    sheet.append_row(row)


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

# ---------------- Field dictionary per Word spec ----------------
# Source for the spec: "Engine Machinery Log Abstract - Proposal" (user-provided Word document).

VOYAGE_FIELDS = {
    "Vessel condition Laden/ballast": {"type": "select", "options": ["Laden", "Ballast"]},
    "Nominal slip %": {"type": "number"},
    # FO consumption split
    "FO consumption - ME (t/day)": {"type": "number"},
    "FO consumption - AE (t/day)": {"type": "number"},
    "FO consumption - Boiler (t/day)": {"type": "number"},
    "Main Engine RPM": {"type": "number"},
    "Main Engine load %": {"type": "number"},
    "FO index": {"type": "number"},
    "Turbocharger RPM": {"type": "number"},
}

ME_TEMPS_FIELDS = {
    "Exhaust gas temp before T/C (°C)": {"type": "number"},
    "Exhaust gas temp after T/C (°C)": {"type": "number"},
    # Per-cylinder exhaust temps
    **{f"Exhaust gas temp cyl {i} (°C)": {"type": "number"} for i in range(1, 7)},
    # Under piston temps per cylinder
    **{f"Under piston temp cyl {i} (°C)": {"type": "number"} for i in range(1, 7)},
    "Exhaust temp before EGB (°C)": {"type": "number"},
    "Exhaust temp after EGB (°C)": {"type": "number"},
    "Air cooler water temp IN (°C)": {"type": "number"},
    "Air cooler water temp OUT (°C)": {"type": "number"},
    "Air cooler gas temp IN (°C)": {"type": "number"},
    "Air cooler gas temp OUT (°C)": {"type": "number"},
    "Cooling water temp IN (°C)": {"type": "number"},
    "Cooling water temp OUT (°C)": {"type": "number"},
    "Stern tube bearings temp (°C)": {"type": "number"},
}

ME_PRESS_FIELDS = {
    "Scavenge air pressure (bar)": {"type": "number"},
    "ΔP ME air cooler (bar)": {"type": "number"},
    "ΔP Exhaust Gas boiler (bar)": {"type": "number"},
    "ΔP ME T/C air inlet filter (bar)": {"type": "number"},
    "FO inlet pressure (bar)": {"type": "number"},
    "LO inlet pressure (bar)": {"type": "number"},
    "Turbocharger LO inlet pressure (bar)": {"type": "number"},
    "Cooling water inlet pressure (bar)": {"type": "number"},
    "Hydraulic oil pressure after filter (bar)": {"type": "number"},
    "FO filter flushing amount per day (l)": {"type": "number"},
    "LO filter flushing amount per day (l)": {"type": "number"},
    "ME water-in-oil monitor %": {"type": "number"},
}

ME_LO_FIELDS = {
    "ME sump LO consumption (l)": {"type": "number"},
    "ME cylinder oil consumption per day (l)": {"type": "number"},
    "ME Running Hours": {"type": "number"},
}

AE_FIELDS = {
    # Highest AE exhaust gas temperature
    **{f"AE{i} highest exhaust gas temp (°C)": {"type": "number"} for i in [1, 2, 3]},
    # Turbocharger temps
    **{f"AE{i} T/C inlet temp (°C)": {"type": "number"} for i in [1, 2, 3]},
    **{f"AE{i} T/C outlet temp (°C)": {"type": "number"} for i in [1, 2, 3]},
    # LO consumption
    **{f"AE{i} LO consumption (l)": {"type": "number"} for i in [1, 2, 3]},
    # Average load & Running hours
    **{f"AE{i} average load %": {"type": "number"} for i in [1, 2, 3]},
    **{f"AE{i} Running Hours": {"type": "number"} for i in [1, 2, 3]},
}

# Name → dict mapping to render the form
NEW_SECTIONS = {
    "Voyage Condition": VOYAGE_FIELDS,
    "Main Engine Temperatures": ME_TEMPS_FIELDS,
    "Main Engine Pressures": ME_PRESS_FIELDS,
    "Main Engine LO consumption": ME_LO_FIELDS,
    "AE Related Information": AE_FIELDS,
}

# ---------------- TAB 1: Data Entry ----------------
with tab1:
    st.header("🔧 Add Engine Log Entry (per Engine Machinery Log Abstract)")
    vessel_list = [
        "Nordmarlin", "Norddolphin", "Nordindepndence", "Nordpenguin", "Nordtokyo",
        "Nordorse", "Nordtulip", "Nordlotus", "Nordorchid", "Nordsymphony",
        "Angelic Anna", "Radiant Reb",
    ]

    date = st.date_input("Date")
    vessel = st.selectbox("Select Vessel", vessel_list)

    # Form dict
    form_data = {"Date": date.strftime("%Y-%m-%d"), "Vessel": vessel}

    with st.form("engine_log_form_new"):
        # Voyage condition first (compact controls)
        with st.expander("Voyage Condition", expanded=True):
            for label, meta in VOYAGE_FIELDS.items():
                key = label
                if meta["type"] == "number":
                    form_data[key] = st.number_input(label, step=0.1)
                elif meta["type"] == "select":
                    form_data[key] = st.selectbox(label, meta["options"])
                else:
                    form_data[key] = st.text_input(label)

        # Other sections
        for section_name, fields in NEW_SECTIONS.items():
            if section_name == "Voyage Condition":
                continue
            with st.expander(section_name):
                for label, meta in fields.items():
                    key = label
                    if meta["type"] == "number":
                        form_data[key] = st.number_input(label, step=0.1)
                    elif meta["type"] == "select":
                        form_data[key] = st.selectbox(label, meta["options"])
                    else:
                        form_data[key] = st.text_input(label)

        remarks = st.text_area("Remarks")
        form_data["Remarks"] = remarks

        if st.form_submit_button("Submit Engine Log Entry"):
            append_engine_log(form_data)
            st.success("Engine log entry saved.")
            st.rerun()

# ---------------- TAB 2: Dashboard ----------------
with tab2:
    st.header("📊 Engine Log Dashboard")
    df = load_data()

    if df.empty or "Vessel" not in df.columns or df["Date"].isna().all():
        st.warning("No valid data found in engine log file.")
    else:
        df = df[df["Date"].notna()].copy()
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month

        vessels = sorted([v for v in df["Vessel"].dropna().unique()])
        selected_vessel = st.selectbox("Select Vessel", vessels)
        selected_year = st.selectbox("Select Year", sorted(df["Year"].dropna().unique()))

        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
            7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
        }
        available_months = sorted(df[df["Year"] == selected_year]["Month"].dropna().unique())
        selected_month = st.selectbox("Select Month", [month_names[m] for m in available_months])
        month_to_num = {v: k for k, v in month_names.items()}
        selected_month_num = month_to_num[selected_month]

        filtered = df[
            (df["Vessel"] == selected_vessel)
            & (df["Year"] == selected_year)
            & (df["Month"] == selected_month_num)
        ].copy()

        if filtered.empty:
            st.warning("No data available for the selected filters.")
        else:
            view_option = st.selectbox(
                "Select Data View",
                [
                    "🧭 Voyage Condition",
                    "🌡️ Main Engine Temperatures",
                    "⚙️ Main Engine Pressures",
                    "🛢️ Main Engine LO consumption",
                    "🔌 AE Related Information",
                ],
            )

            VIEW_COLUMNS = {
                "🧭 Voyage Condition": [
                    "Vessel condition Laden/ballast",
                    "Nominal slip %",
                    "FO consumption - ME (t/day)",
                    "FO consumption - AE (t/day)",
                    "FO consumption - Boiler (t/day)",
                    "Main Engine RPM",
                    "Main Engine load %",
                    "FO index",
                    "Turbocharger RPM",
                ],
                "🌡️ Main Engine Temperatures": list(ME_TEMPS_FIELDS.keys()),
                "⚙️ Main Engine Pressures": list(ME_PRESS_FIELDS.keys()),
                "🛢️ Main Engine LO consumption": list(ME_LO_FIELDS.keys()),
                "🔌 AE Related Information": list(AE_FIELDS.keys()),
            }

            sel_cols = [c for c in VIEW_COLUMNS[view_option] if c in filtered.columns]
            display_df = filtered[["Date"] + sel_cols].sort_values("Date")
            display_df.columns = [c.strip() for c in display_df.columns]

            # Add Average row for numeric cols
            avg_row = {}
            for col in display_df.columns:
                if col == "Date":
                    avg_row[col] = "Average"
                elif pd.api.types.is_numeric_dtype(display_df[col]):
                    avg_row[col] = display_df[col].mean()
                else:
                    avg_row[col] = ""

            avg_df = pd.concat([display_df, pd.DataFrame([avg_row])], ignore_index=True)
            st.markdown(
                "<style>thead th {font-size: 10px !important;} tbody td {font-size: 12px !important;}</style>",
                unsafe_allow_html=True,
            )
            st.dataframe(avg_df, use_container_width=True, height=500)

            # One simple example chart per view (optional & lightweight)
            if view_option == "🧭 Voyage Condition" and "Nominal slip %" in display_df.columns:
                st.markdown("### 📈 Nominal Slip – Trend")
                plot_df = display_df[["Date", "Nominal slip %"]].dropna()
                if not plot_df.empty:
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.plot(plot_df["Date"], plot_df["Nominal slip %"], marker="o")
                    ax.set_title("Nominal Slip %")
                    ax.set_xlabel("Date")
                    ax.set_ylabel("%")
                    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
                    ax.grid(True)
                    st.pyplot(fig)
                else:
                    st.info("No data available for plotting.")

            if view_option == "🛢️ Main Engine LO consumption" and "ME Running Hours" in display_df.columns:
                st.markdown("### 📈 ME Running Hours – Trend")
                plot_df = display_df[["Date", "ME Running Hours"]].dropna()
                if not plot_df.empty:
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.plot(plot_df["Date"], plot_df["ME Running Hours"], marker="o")
                    ax.set_title("ME Running Hours")
                    ax.set_xlabel("Date")
                    ax.set_ylabel("Hours")
                    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
                    ax.grid(True)
                    st.pyplot(fig)
                else:
                    st.info("No data available for plotting.")
