import pandas as pd                          # to build and write out our table
import streamlit as st

df = pd.read_csv('ufc_scorecards.csv')

@st.cache_data
def load_data():
    return pd.read_csv("ufc_scorecards.csv")