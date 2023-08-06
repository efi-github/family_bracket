import streamlit as st

st.set_page_config(
    page_title="Turnier Raten",
    page_icon="⚽",
)

st.write("# Fittschen WM 2023 Turnier raten!🔥⚽")

#st.sidebar.success("Select a demo above.")

st.markdown(
    """
## Pages: 
### 👈 Raten
Gebe deine Tipps ein 🔥🔥
  
  ### 👈 Punkte Übersicht
Die derzeitigen Punkte.
Punktezahl wächst im laufe des Turniers exponentiell.
Beispiel im achtelfinale hat man eine 1/2 chance richtig zu raten --> 2p.
Im finale hat man eine 1/16 chance richtig zu raten --> 16p.""")