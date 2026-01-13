import streamlit as st
import plotly.express as px
import pandas as pd
from start import get_all_data

st.title("UCLA Men's Tennis Dashboard")

# Get data directly without CSV
@st.cache_data
def load_data():
    return get_all_data()

data = load_data()

# Display current schedule
st.header("Current Schedule")
if not data['current_schedule'].empty:
    st.dataframe(data['current_schedule'], width='stretch')
else:
    st.write("No schedule data available")

# Display roster
st.header("Team Roster")
if not data['roster'].empty:
    st.dataframe(data['roster'], width='stretch')
else:
    st.write("No roster data available")

# Display historical seasons
st.header("Historical Results")
season = st.selectbox("Select Season", list(data['seasons'].keys()))
if season and season in data['seasons']:
    st.dataframe(data['seasons'][season], width='stretch')
    
    # Performance line graph
    st.header(f"Performance Graph ({season})")
    
    df = data['seasons'][season].copy()
    
    # Create score change: +1 for W, -1 for L, 0 otherwise
    def compute_score(result):
        if pd.isna(result) or result == "":
            return 0
        return 1 if result.upper().startswith("W") else -1 if result.upper().startswith("L") else 0
    
    df["ScoreChange"] = df["Result"].apply(compute_score)
    df["DateParsed"] = pd.to_datetime(df["Date"], format="%m-%d-%Y", errors="coerce")
    
    # Filter valid dates and sort
    df = df.dropna(subset=["DateParsed"]).sort_values("DateParsed")
    df["CumulativeScore"] = df["ScoreChange"].cumsum()
    
    if not df.empty:
        fig = px.line(
            df, x="DateParsed", y="CumulativeScore", 
            title=f"Cumulative Performance ({season})",
            markers=True
        )
        fig.update_layout(
            yaxis_title="Cumulative Score (+1 W, -1 L)",
            xaxis_title="Date"
        )
        st.plotly_chart(fig, config={'displayModeBar': False})