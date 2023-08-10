import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import copy
import json
import pandas as pd
from pprint import pprint
import pickle as pkl
import iso8601
from dateutil import tz
local_tz = tz.tzlocal()

green = "#90EE90"
red = "#FF7377"
grey = "#cfc9c4"
blue = "#ECECFD"

def mermaid(code: str) -> None:
    components.html(
        f"""
        <pre class="mermaid">
            {code}
        </pre>

        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
        </script>
        """, height=250
    )

country_codes = {
    "Switzerland": "SUI",
    "Spain": "ESP",
    "Netherlands": "NED",
    "South Africa": "ZAF",
    "Japan": "JPN",
    "Norway": "NOR",
    "Sweden": "SWE",
    "United States": "USA",
    "Australia": "AUS",
    "Denmark": "DEN",
    "France": "FRA",
    "Morocco": "MAR",
    "England": "ENG",
    "Nigeria": "NGA",
    "Columbia": "COL",
    "Colombia": "COL",
    "Jamaica": "JAM",
    "Not Decided": "___"
}

def load_data(sheets_url):
    csv_url = sheets_url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url)


@st.cache_data(ttl=60)
def load_live_data():
    df = load_data(st.secrets["public_gsheets_url"])
    df_transpose = df.transpose(copy=True)
    dic_inv = df_transpose.to_dict()
    return dic_inv

def load_players():
    try:
        with open('player_states.pkl', 'rb') as f:
            players = pkl.load(f)
        return players
    except FileNotFoundError:
        players = {}
        return players


def new_player(username):
    player = {"name": username, "matches": None, "submitted": False}
    matches = copy.deepcopy(st.session_state["live_data"])
    for key, temp in matches.items():
        temp["datetime"] = iso8601.parse_date(temp["datetime"])
        temp["status"] = "EMPTY"
    player["matches"] = matches
    return player

def get_player(username):
    players = load_players()
    if username in players:
        return players[username]
    else:
        return new_player(username)

def get_status(match, live_match):
    winner = live_match["winner"]
    done = (winner != "NONE")
    time = iso8601.parse_date(live_match["datetime"])
    started = (time < datetime.now(local_tz))
    correct = winner == match["prediction"]
    predicted = (match["prediction"] !="Not Decided")

    if started and not predicted:
        return "NOT_VOTED"
    if done and correct:
        return "CORRECT"
    if done and not correct:
        return "INCORRECT"
    else:
        return "EMPTY"

def update_player():
    matches = st.session_state["player"]["matches"]
    live_data = st.session_state["live_data"]
    for match, live_match in zip(matches.values(), live_data.values()):
        match["status"] = get_status(match, live_match)

def mermaid_string(key, match, live_match):
    teamA = country_codes[match["TeamA"]]
    teamB = country_codes[match["TeamB"]]
    if match["prediction"] == match["TeamA"]:
        teamA = "<b><u>"+ teamA + "</u></b>"
    if match["prediction"] == match["TeamB"]:
        teamB = "<b><u>"+ teamB + "</u></b>"

    info = "<br>" + country_codes[live_match["TeamA"]] + " " + str(live_match["goalsA"]) +  " : " + str(live_match["goalsB"]) + " "+ country_codes[live_match["TeamB"]]
    if match["status"]=="EMPTY":
        info = ""
    string = f"M{key}[{teamA + ' vs ' + teamB + '<small>' + info + '</small>'}] --> M{match['nextMatch']}\n"
    if match['nextMatch'] == 0:
        string = f"M{key}[{teamA + ' vs ' + teamB + info}]\n"
    return string

def get_style(key, match):
    color = blue
    if match["status"] == "CORRECT":
        color = green
    if match["status"] == "INCORRECT":
        color = red
    if match["status"] == "NOT_VOTED":
        color = grey
    string = f"style M{key} fill:{color},stroke:#8E72D4\n"
    return string

def display_player_bracket(player):
    matches = player["matches"]
    live_matches = st.session_state["live_data"]
    string = "graph TD\n"
    for key, match in matches.items():
        string += mermaid_string(key, match, live_matches[key])
        string += get_style(key, match)
    mermaid(string)

def process_choice(index):
    matches = st.session_state["player"]["matches"]
    match = matches[index]
    choice = st.session_state[f"selectbox_{index}"]

    if choice == "Select a Team":
        choice = "Not Decided"
    if match["prediction"] != "Not Decided" and match["nextMatch"] != 0:

        old_team = match["prediction"]
        current_match = match
        next_match = matches[current_match["nextMatch"]]
        next_match[current_match["nextTeam"]] = choice
        while (next_match["prediction"] == old_team) and (next_match["nextMatch"]!=0):
            next_match["prediction"] = choice
            current_match = next_match
            next_match = matches[current_match["nextMatch"]]
            next_match[current_match["nextTeam"]] = choice
    match["prediction"] = choice
    if match["nextMatch"] != 0:
        matches[match["nextMatch"]][match["nextTeam"]] = choice
def display_match(index):
    matches = st.session_state["player"]["matches"]
    match = matches[index]
    answers = ["Select a Team", match['TeamA'], match['TeamB']]
    locked = False
    if st.session_state["player"]["submitted"]:
        locked = True
    if match["status"] == "NOT_VOTED":
        locked = True
        answers[0] = "Game already started/finished"
    selection_index = 0
    if match["prediction"] != "Not Decided":
        if match["prediction"] in answers:
            selection_index = answers.index(match["prediction"])
        else:
            match["prediction"] = "Not Decided"


    prompt = f"Who will win, {match['TeamA']} or {match['TeamB']}?"

    st.selectbox(prompt, answers, disabled=locked, index= selection_index, key=f"selectbox_{index}", on_change=process_choice, args = (index,))


def display_player_form(thing):
    st.write("### Round of 16:")
    for i in range(8):
        display_match(i)
    st.write("### Quarterfinal:")
    for i in range(8, 12):
        display_match(i)
    st.write("### Semifinal:")
    for i in range(12, 14):
        display_match(i)
    st.write("### Final:")
    display_match(14)


def can_submit():
    res = False
    matches = st.session_state["player"]["matches"]
    for m in matches.values():
        if m["prediction"] == "Not Decided" and m["status"]!= 'NOT_VOTED':
            res = True
    if st.session_state["player"]["submitted"] == True:
        res = True
    return res

def save_state(players):
    with open('player_states.pkl', 'wb') as f:
        pkl.dump(players, f)

def submit_player_data():
    players = load_players()
    st.session_state["player"]["submitted"] = True
    players[st.session_state["username"]] = st.session_state["player"]
    save_state(players)

def process_username():
    st.session_state["live_data"] = load_live_data()
    st.session_state["player"] = get_player(st.session_state["username"])