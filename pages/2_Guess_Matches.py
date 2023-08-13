import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import copy
import json
import pandas as pd
from pprint import pprint
import pickle as pkl
import iso8601
from dateutil import tz
import time
from utilities import *
local_tz = tz.tzlocal()

st.set_page_config(
    page_title="Guess",
    page_icon="🤔",
)

def match_display(match, live_match):
    date = iso8601.parse_date(live_match['datetime'])
    delta = date - datetime.now(tz=local_tz)

    disable = False
    if "submitted" in match:
        disable = match["submitted"]
    if delta < timedelta(minutes=0):
        disable = True



    st.write(f"Match: {live_match['TeamA']} vs {live_match['TeamB']}")
    if delta < timedelta(minutes=0):
        st.error(f"closed")
    elif delta < timedelta(minutes=30):
        st.error(f"closes soon!")
    col1, col2 = st.columns(2)
    number_a = 0
    number_b = 0
    with col1:
        value = 0
        if "goalsAp" in match:
            value = match["goalsAp"]
        number_a = st.number_input(f"Insert goal prediction for {live_match['TeamA']}",value=value, step=1, min_value=0, disabled=disable, key=f"Match: {match['TeamA']} vs {match['TeamB']} col1")
    with col2:
        value = 0
        if "goalsBp" in match:
            value = match["goalsBp"]
        number_b = st.number_input(f"Insert goal prediction for {live_match['TeamB']}",value=value, step=1, min_value=0, disabled=disable, key=f"Match: {match['TeamA']} vs {match['TeamB']} col2")

    def submit_player_data_qf():
        match["goalsAp"] = number_a
        match["goalsBp"] = number_b
        match["submitted"] = True
        players = load_players()
        players[st.session_state["username"]] = st.session_state["player"]
        save_state(players)

    st.button("Submit", disabled=disable, key = f"Match: {match['TeamA']} vs {match['TeamB']}", on_click=submit_player_data_qf)
    if "submitted" in match and match["submitted"]:
        st.success("Match submitted")


def display_games(player, live_data, start, end):
    for i in range(start, end):
        match_display(player["matches"][i], live_data[i])


st.write("# Guess the current Matches!")
st.text_input("Please enter a nickname to start", key="username", on_change=process_username)


if "player" in st.session_state and len(st.session_state["username"]) >0:
    st.session_state["live_data"] = load_live_data()
    update_player()
    display_games(st.session_state["player"],st.session_state["live_data"], 12, 14)
