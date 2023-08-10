import streamlit as st
import pandas as pd
import numpy as np
import pickle as pkl
from pprint import pprint
import iso8601
from datetime import datetime
import streamlit.components.v1 as components
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
st.set_page_config(page_title="Leaderboard", page_icon="🌍")
def load_data(sheets_url):
    csv_url = sheets_url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url)
def load_players():
    try:
        with open('player_states.pkl', 'rb') as f:
            players = pkl.load(f)
        return players
    except FileNotFoundError:
        players = {}
        return players

def load_live_data():
    df = load_data(st.secrets["public_gsheets_url"])
    df_transpose = df.transpose(copy=True)
    dic_inv = df_transpose.to_dict()
    return dic_inv

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

def update_player(player, live_data):
    matches = player["matches"]
    for match, live_match in zip(matches.values(), live_data.values()):
        match["status"] = get_status(match, live_match)

def calculate_bracket_points(player, live_data, match_number):
    max_lim = int(max(list(player["matches"].keys())))
    if match_number < 0 or player["matches"][match_number]["status"]=="NOT_VOTED":
        return 1
    next_l = 15 - ((15-match_number) * 2 + 1)
    next_r = 15 - ((15-match_number) * 2)
    res = calculate_bracket_points(player, live_data, next_l) + calculate_bracket_points(player, live_data, next_r)
    return res


def calculate_points(player, live_data):
    points_overview = {"description":[], "match": [], "points": []}
    update_player(player, live_data)
    matches = player["matches"]
    double_dict = {}
    points = 0
    match_points = 0
    for i, m, l_m in zip(matches.keys(), matches.values(), live_data.values()):
        if m["status"] == "CORRECT":
            country = m["prediction"]
            if country not in double_dict:
                double_dict[country] = 1
            point_cur = float(calculate_bracket_points(player, live_data, int(i)))
            double_dict[country] *= 2
            points_overview["description"].append(f"Correctly predicted {country} ({country_codes[country]}) win in: ")
            points_overview["match"].append(f"{country_codes[m['TeamA']]} vs {country_codes[m['TeamB']]}")
            points_overview["points"].append(point_cur)
            #points_overview["points"].append(float(double_dict[country]))
            # points_overview["match points"].append(float(calculate_points_s(m, l_m)))
            # points_overview["total"].append(float(points_overview["bracket points"][-1]+points_overview["match points"][-1]))
            points += point_cur
            match_points += calculate_points_s(m, l_m)
    return points, points_overview, match_points
def mermaid_string(key, match, live_match):
    teamA = country_codes[match["TeamA"]]
    teamB = country_codes[match["TeamB"]]
    if match["prediction"] == match["TeamA"]:
        teamA = "<b><u>"+ teamA + "</u></b>"
    if match["prediction"] == match["TeamB"]:
        teamB = "<b><u>"+ teamB + "</u></b>"

    info = "<br>" + country_codes[live_match["TeamA"]] + " " + str(live_match["goalsA"]) +  " : " + str(live_match["goalsB"]) + " "+ country_codes[live_match["TeamB"]]
    if match["status"]=="EMPTY":
        if (live_match["TeamA"] != "Not Decided") or (live_match["TeamB"] != "Not Decided"):
            info = "<br>" + country_codes[live_match["TeamA"]] +  " : " + country_codes[live_match["TeamB"]]
        else:
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

def player_match_predictions(player):
    res = False
    for match in player["matches"].values():
        if "submitted" in match:
            if match["submitted"] == True:
                return True

def calculate_points_s(match, live_match):
    if "submitted" in match and live_match["done"]:
        predGA= match["goalsAp"]
        predGB = match["goalsBp"]
        GA = live_match["goalsA"]
        GB = live_match["goalsB"]
        diff_a = predGA - GA
        diff_b = predGB - GB
        diff_pAB = predGA - predGB
        diff_AB = GA - GB
        print(f"{predGA}:{predGB}, {GA}:{GB}")
        print(diff_a)
        print(diff_b)
        if diff_a == 0 and diff_b == 0:
            return 5
        if diff_pAB == diff_AB:
            return 4
        if diff_AB > 0 and diff_pAB > 0:
            return 3
        if diff_AB < 0 and diff_pAB < 0:
            return 3
    return 0
def display_match_predictions(player):
    res = {"game":[], "prediction":[], "result": [], "points":[]}
    for match, live_match in zip(player["matches"].values(), st.session_state["live_data"].values()):
        if "submitted" in match and match["submitted"] == True:
            print(match)
            res["game"].append(f"{live_match['TeamA']} vs {live_match['TeamB']}")
            res["prediction"].append(f"{match['goalsAp']} : {match['goalsBp']}")
            if live_match["done"]:
                res["result"].append(f"{live_match['goalsA']} : {live_match['goalsB']}")
            else:
                res["result"].append(f"NA")
            res["points"].append(str(calculate_points_s(match, live_match)))

    df_pred = pd.DataFrame(res)
    st.dataframe(df_pred, use_container_width=True, hide_index=True)
    return

st.markdown("# Leaderboard")



players = load_players()

live_data = load_live_data()
leaderboard_data = {"names":[], "bracket points":[], "match points":[]}
for name, player in players.items():
    leaderboard_data["bracket points"].append(float(calculate_points(player, live_data)[0]))
    leaderboard_data["match points"].append(float(calculate_points(player, live_data)[2]))
    leaderboard_data["names"].append(name)

df = pd.DataFrame(leaderboard_data)
df = df.sort_values("bracket points", ascending=False)
df = df.reset_index(drop=True)
st.dataframe(df, use_container_width=True, hide_index=True)

# Create a list of user names
user_names = df["names"]

# Create a select box

if len(user_names)>0:
    user_names = ["Select a user"] + list(user_names)

    args = st.experimental_get_query_params()
    index = 0
    if "selected_user" in args.keys():
        if args["selected_user"][0] in user_names:
            index = user_names.index(args["selected_user"][0])

    def change_user():
        selected_user = st.session_state["selected_user"]
        if selected_user != "Select a user":
            st.experimental_set_query_params(selected_user=selected_user)
        else:
            st.experimental_set_query_params()

    selected_user = st.selectbox('Show a users predictions', user_names, key= "selected_user", index=index, on_change=change_user)

    if selected_user != "Select a user":
        st.session_state["live_data"] = live_data
        if players[selected_user]["submitted"] == True:
            st.write("### Bracket Prediction")
            display_player_bracket(players[selected_user])
            player_points, point_overview, match_points = calculate_points(players[selected_user], live_data)
            df_points = pd.DataFrame(point_overview)
            st.dataframe(df_points, use_container_width=True, hide_index=True)
        if player_match_predictions(players[selected_user]):
            st.write("### Match Prediction")
            display_match_predictions(players[selected_user])


    def dict_to_csv(dictionary):
        rows = []
        for user, user_info in dictionary.items():
            for match_id, match_info in user_info['matches'].items():
                row = {'user': user}
                fields_to_include = ['TeamA', 'TeamB', 'nextMatch', 'nextTeam', 'prediction', 'status']
                for key in fields_to_include:
                    row[key] = match_info.get(key)
                row["goal prediction A"] = "NA"
                row["goal prediction B"] = "NA"
                if "submitted" in match_info and match_info["submitted"]:
                    row["goal prediction A"] = match_info["goalsAp"]
                    row["goal prediction B"] = match_info["goalsBp"]
                rows.append(row)
        df = pd.DataFrame(rows)
        return df.to_csv().encode('utf-8')

    # Use the function
    csv = dict_to_csv(players)
    st.download_button(
        label="Download player-data as CSV",
        data=csv,
        file_name='player_data.csv',
        mime='text/csv',
    )


