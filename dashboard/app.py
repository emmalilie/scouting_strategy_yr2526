import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------
# STREAMLIT CONFIG
# -------------------------
st.set_page_config(page_title="UCLA Men's Tennis Dashboard", layout="wide")
st.title("🎾 UCLA Men's Tennis Dashboard — Tables + Season Graph")

# -------------------------
# LOAD ROSTER (fixed 25–26 CSV)
# -------------------------
roster_csv = "ucla_mens_tennis_roster.csv"
roster_df = pd.read_csv(roster_csv)

# -------------------------
# LOAD MULTI-YEAR SCHEDULE EXCEL
# -------------------------
excel_file = "ucla_mens_tennis_results_by_year.xlsx"
xls = pd.ExcelFile(excel_file)

# Get all sheet names as available seasons
seasons = xls.sheet_names

# Year selector
selected_season = st.selectbox("Select Season", seasons)

# Load schedule for selected year
schedule_df = pd.read_excel(xls, sheet_name=selected_season)

# Replace missing results (like '-') with N/A
schedule_df["Result"] = schedule_df["Result"].replace("-", "N/A").fillna("N/A")

# Ensure opponent column exists
if "Opponent" not in schedule_df.columns:
    schedule_df["Opponent"] = "Unknown"

# -------------------------
# STREAMLIT LAYOUT
# -------------------------

# --- Roster + Stats ---
st.header("👟 Player Roster & Stats (2025–26)")
st.dataframe(roster_df, use_container_width=True)

# --- Match Schedule ---
st.header(f"📅 Match Schedule ({selected_season})")

opponent_filter = st.text_input("Filter schedule by opponent (leave blank for all)")
filtered_schedule = schedule_df
if opponent_filter:
    filtered_schedule = schedule_df[
        schedule_df["Opponent"].str.contains(opponent_filter, case=False, na=False)
    ]

# Display key columns
display_cols = ["Date", "Opponent", "Location", "Result"]
st.dataframe(filtered_schedule[display_cols], use_container_width=True)

# -------------------------
# PERFORMANCE LINE GRAPH
# -------------------------
# Prepare data for plotting
plot_df = filtered_schedule.copy()

# Create a ScoreChange column: +1 for W, -1 for L, 0 otherwise
def compute_score(result):
    if result.upper().startswith("W"):
        return 1
    elif result.upper().startswith("L"):
        return -1
    else:
        return 0

plot_df["ScoreChange"] = plot_df["Result"].apply(compute_score)

# Parse dates
plot_df["DateParsed"] = pd.to_datetime(plot_df["Date"], format="%m-%d-%Y", errors="coerce")

# Drop rows with invalid dates
plot_df = plot_df.dropna(subset=["DateParsed"])

# Sort by date
plot_df = plot_df.sort_values("DateParsed").reset_index(drop=True)

# Compute cumulative score
plot_df["CumulativeScore"] = plot_df["ScoreChange"].cumsum()

# Create line plot
fig = px.line(
    plot_df,
    x="DateParsed",
    y="CumulativeScore",
    text="Opponent",
    title=f"Cumulative Season Performance ({selected_season})",
    markers=True
)

fig.update_traces(textposition="top right", textfont=dict(size=10))
fig.update_layout(
    yaxis_title="Cumulative Score (+1 for W, -1 for L)",
    xaxis_title="Date",
    xaxis=dict(tickangle=-45),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)
