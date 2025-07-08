import pandas as pd
import streamlit as st
import base64
import plotly.express as px
import plotly.graph_objects as go

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
start_year, end_year = st.sidebar.slider("Years", 1996, 2025, (2000, 2010))
# 1) Mask rows to the chosen years
mask = df["year"].between(start_year, end_year)
# 2) Pull out the events in their original CSV order,
#    dropping duplicates but preserving first‐seen order:
ordered = df.loc[mask, "event"].unique().tolist()
# 3) Prepend “All Events” so it’s always first:
choices = ["All Events"] + ordered
# 4) Show the selectbox
selected_event = st.sidebar.selectbox("Select an Event", choices)

# Returns dataframe that determines ratio of method victories
def method_ratio(df):
    # count judge‐cards per method…
    counts = df["method"].value_counts()
    # …then divide by 3 to get bouts-per-method
    bout_counts = counts / 3
    return bout_counts.sort_index()

def count_split(df):
    
    # Counts only methods with split decisions
    split_df = df[df["method"].str.contains("Split", case=False, na=False)].copy()

    judges = []
    
    # Goes through each (event, bout) tuple
    for (_, bout_group) in split_df.groupby(["event","bout"]):
        # Takes column score and splits into ints
        scores = bout_group["score"].str.split("-", expand=True).astype(int)
        # Turns score differnece into series
        diffs = scores.iloc[:, 0] - scores.iloc[:, 1]

        for idx in diffs[diffs < 0].index:
            judges.append(bout_group.at[idx, "judge"])

    counts = pd.Series(judges).value_counts()
    return counts.reset_index().rename(
        columns={"index": "judge", "count": "dissent_count"}
    )


# 2. One‐off trigger:
if st.sidebar.button("Analyze"):

    mask_year = (df.year >= start_year) & (df.year <= end_year)
    df_year = df[mask_year]
    
    if selected_event == "All Events":
        to_plot = df_year
        title = f"All Events ({start_year}-{end_year})"
    else:
        to_plot = df_year[df_year.event == selected_event]
        title = f"{selected_event} ({start_year}-{end_year})"

    # 3. Creates Chart
    ratio = method_ratio(to_plot)
    st.subheader(f"Decision-Type Ratio for {title}")
    
    # same DataFrame as above
    chart_df = ratio.reset_index()
    chart_df.columns = ["Decision Method", "Bouts"]

    fig = px.bar(
        chart_df,
        x="Decision Method",
        y="Bouts",
        color="Decision Method",
        title=f"Decision-Type Ratio for {title}",
        labels={"Bouts": "Number of Bouts", "Decision Method": "Decision Type"},
    )
    fig.update_layout(
        hoverdistance=50   # how many pixels away the cursor can be
    )

    # 2. Overlay invisible, large markers on just the Unknown bars:
    unknown_df = chart_df[chart_df["Decision Method"].str.startswith("Unknown")]
    fig.add_trace(
        go.Scatter(
            x=unknown_df["Decision Method"],
            y=unknown_df["Bouts"],
            mode="markers",
            marker=dict(size=60, opacity=0),   # big & invisible
            hoverinfo="text",
            hovertext=[f"{m}: {b}" for m, b in zip(unknown_df["Decision Method"], unknown_df["Bouts"])],
            showlegend=False
        )
    )

    judge_df = count_split(to_plot)

    if not judge_df.empty:
        fig2 = px.bar(
            judge_df,
            x="judge",
            y="dissent_count",
            title="Judges with Most Split-Decision Dissents",
            labels={"dissent_count": "Number of Dissenting Cards", "judge": "Judge"}
        )
        st.subheader("Split-Decision Dissent by Judge")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.write("No Split Decisions in this selection.")
    
    st.plotly_chart(fig, use_container_width=True) 

if st.sidebar.button("Decision Trends Over the Years"):
    yearly_cards = (
        df
        .groupby("year")["method"]
        .value_counts()
        .unstack()
        .fillna(0)
    )

    # 2) Convert to bouts (3 cards per bout)
    yearly_bouts = yearly_cards / 3

    st.subheader("Yearly Decision Counts (in Bouts)")
    st.line_chart(yearly_bouts)