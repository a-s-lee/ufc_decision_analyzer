import pandas as pd
import streamlit as st
import base64

# Cache the load (so Streamlit doesn’t re-read the file on every interaction)
@st.cache_data
def load_data():
    return pd.read_csv("../ufc_scorecards.csv")

df = load_data()

# add page_icon l8r 
st.set_page_config(page_title="UFC Bout Predictor", layout="wide")
# Loads Google Font
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# Styled "heading" without triggering Streamlit's header logic (copy-link)
st.markdown("""
    <div style='text-align: center;'>
        <div style='
            background-color: #A50C1D;
            color: white;
            display: inline-block;
            padding: 20px 35px;
            font-family: Bebas Neue;
            font-size: 3em;
            font-weight: bold;
            border-radius: 10px;
        '>
            UFC DECISION ANALYSIS
        </div>
    </div>
""", unsafe_allow_html=True)

# Sets background image
def set_bg(image_path):
    # This reads the image as raw bytes, not as text
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

set_bg("../bg.jpg")

# Year Slider (start_year & end_year is the user's input)
# 1. Always reactive inputs:
start_year, end_year = st.sidebar.slider("Years", 1996, 2025, (2000, 2010))
available = df.loc[df.year.between(start_year, end_year), "event"].unique()
events = ["All Events"] + sorted(available)
selected_event = st.sidebar.selectbox("Select an Event", events)

# 2. One‐off trigger:
if st.sidebar.button("Analyze"):
    filtered = df[df.year.between(start_year, end_year)]
    if selected_event != "All Events":
        filtered = filtered[filtered.event == selected_event]
    # …generate charts, metrics, etc.


