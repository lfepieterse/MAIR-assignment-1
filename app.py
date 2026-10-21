"""Run from the project folder: python -m streamlit run app.py"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import joblib
import streamlit as st

from dialogue_manager_formal import transition as formal_transition
from dialogue_manager_friendly import transition as friendly_transition
from dialogue_state import create_dialogue, END, RECOMMEND
from restaurant_repository import load_restaurants
from models import get_embeddings
from study_flow import chatbot_order, record_recommendation


ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "study_data" / "sessions.sqlite3"
MODEL_FILE = ROOT / "saved_models" / "original_distilbert_svm.joblib"
SHOW_REASONING = True  # Same setting in BOTH conditions.
TARGET = 3


def now():
    return datetime.now(timezone.utc).isoformat()


def read_study(participant):
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE, timeout=30) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS sessions "
            "(participant INTEGER PRIMARY KEY, content TEXT NOT NULL)"
        )
        row = connection.execute(
            "SELECT content FROM sessions WHERE participant = ?", (participant,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def save_study(study):
    with sqlite3.connect(DATABASE, timeout=30) as connection:
        connection.execute(
            "INSERT INTO sessions (participant, content) VALUES (?, ?) "
            "ON CONFLICT(participant) DO UPDATE SET content = excluded.content",
            (study["participant"], json.dumps(study)),
        )


def event(study, kind, **details):
    study["events"].append({"time": now(), "kind": kind, **details})


def start_round(study):
    condition = study["order"][study["round_index"]]
    transition = formal_transition if condition == "formal" else friendly_transition
    dialogue = create_dialogue()
    dialogue["show_reasoning"] = SHOW_REASONING
    dialogue["restaurants"] = load_restaurants(
        str(ROOT / "data" / "restaurant_info_extended.csv")
    )
    _, greeting = transition(dialogue, "hello")
    study["rounds"].append({
        "condition": condition,
        "dialogue": dialogue,
        "restaurants": [],
        "messages": [{"role": "assistant", "content": greeting}],
    })
    study["stage"] = "chat"
    event(study, "round_started", round=study["round_index"] + 1,
          condition=condition, show_reasoning=SHOW_REASONING)


@st.cache_resource
def load_model():
    return joblib.load(MODEL_FILE)


st.set_page_config(page_title="Restaurant chatbot study")
st.title("Restaurant chatbot study")

if "study" not in st.session_state:
    with st.form("participant_entry"):
        participant = st.text_input("Participant number provided by the researcher")
        submitted = st.form_submit_button("Start or resume")
    if submitted:
        if not participant.isascii() or not participant.isdigit() or int(participant) < 1:
            st.error("Enter the positive participant number provided by the researcher.")
        else:
            participant = int(participant)
            study = read_study(participant)
            if study is None:
                study = {
                    "participant": participant,
                    "order": chatbot_order(participant),
                    "round_index": 0,
                    "rounds": [],
                    "events": [],
                }
                start_round(study)
                save_study(study)
            st.session_state.study = study
            st.rerun()
    st.stop()

study = st.session_state.study
number = study["round_index"] + 1
st.caption(f"Participant {study['participant']} · Round {number} of 2")

if study["stage"] == "complete":
    st.success("Both chat rounds and questionnaires are complete. Thank you!")
    st.download_button(
        "Download study record",
        json.dumps(study, indent=2),
        file_name=f"participant_{study['participant']}.json",
        mime="application/json",
    )
    st.stop()

current = study["rounds"][study["round_index"]]

# Keep the final recommendation visible during the questionnaire pause.
for message in current["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if study["stage"] == "questionnaire":
    st.success("You have received three different restaurant recommendations.")
    st.write(
        f"Please complete the questionnaire for round {number} on the other device. "
        f"Use participant number {study['participant']} and round number {number}. "
        "Leave this browser tab open."
    )
    st.download_button(
        "Download study record so far",
        json.dumps(study, indent=2),
        file_name=f"participant_{study['participant']}_round_{number}.json",
        mime="application/json",
    )
    confirmed = st.checkbox(
        "I have submitted the questionnaire on the other device.",
        key=f"questionnaire_confirmed_{number}",
    )
    label = "Start the second chatbot" if number == 1 else "Finish the study"
    if st.button(label, disabled=not confirmed):
        event(study, "questionnaire_completion_confirmed", round=number)
        if number == 1:
            study["round_index"] = 1
            start_round(study)
        else:
            study["stage"] = "complete"
            event(study, "study_completed")
        save_study(study)
        st.rerun()
    st.stop()

st.write(f"Different recommendations received: {len(current['restaurants'])}/{TARGET}")
st.info(
    "Obtain three different restaurant recommendations. Ask for another restaurant "
    "after a recommendation. If no alternatives remain, change your preferences."
)

dialogue = current["dialogue"]
transition = (formal_transition if current["condition"] == "formal"
              else friendly_transition)

if dialogue["state"] == END:
    st.write("The conversation ended before three recommendations were reached.")
    if st.button("Continue this round with a fresh conversation"):
        restaurants = dialogue["restaurants"]
        dialogue = create_dialogue()
        dialogue["restaurants"] = restaurants
        dialogue["show_reasoning"] = SHOW_REASONING
        current["dialogue"] = dialogue
        _, greeting = transition(dialogue, "hello")
        current["messages"].append({"role": "assistant", "content": greeting})
        event(study, "conversation_reopened", round=number)
        save_study(study)
        st.rerun()
    st.stop()

text = st.chat_input("Type your message", key=f"chat_{number}")
if text and text.strip():
    processed = text.strip().lower()
    before_state = dialogue["state"]
    before_name = (dialogue.get("restaurant") or {}).get("restaurantname")
    with st.spinner("Preparing a response..."):
        saved = load_model()
        if processed == "quit":
            act = "bye"
        else:
            if saved["model_type"] == "tfidf":
                features = saved["extractor"].transform([processed])
            else:
                features = get_embeddings([processed], batch_size=1)
            act = str(saved["model"].predict(features)[0])
        _, response = transition(dialogue, act, processed)

    current["messages"].extend([
        {"role": "user", "content": text},
        {"role": "assistant", "content": response},
    ])
    event(study, "turn", round=number, condition=current["condition"],
          user_text=text, predicted_act=act, response=response)

    if record_recommendation(current, before_state, before_name, dialogue, RECOMMEND):
        event(study, "recommendation", round=number,
              restaurant=current["restaurants"][-1])
    if len(current["restaurants"]) >= TARGET:
        study["stage"] = "questionnaire"
        event(study, "questionnaire_started", round=number)
    save_study(study)
    st.rerun()