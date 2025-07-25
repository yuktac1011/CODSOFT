import streamlit as st
import random
import pandas as pd
import json
import os

DATA_FILE = "game_data.json"

#Function to Load Game Data
def load_data():
    """Loads game history and scores from a JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

#Function to Save Game Data
def save_data(history):
    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=4)

#Initialize Session State
if 'initialized' not in st.session_state:
    st.session_state.history = load_data()
    st.session_state.player_score = 0
    st.session_state.computer_score = 0
    
    # Calculate scores from loaded history
    for round_data in st.session_state.history:
        if "You Win" in round_data["Result"]:
            st.session_state.player_score += 1
        elif "Computer Wins" in round_data["Result"]:
            st.session_state.computer_score += 1
            
    st.session_state.initialized = True


#UI and Game Logic
st.title("Rock Paper Scissors Game")

# Game Logic Function
def determine_winner(player_choice, computer_choice):
    if player_choice == computer_choice:
        return "It's a Tie!"
    elif (player_choice == "Rock" and computer_choice == "Scissors") or \
         (player_choice == "Scissors" and computer_choice == "Paper") or \
         (player_choice == "Paper" and computer_choice == "Rock"):
        return "You Win!"
    else:
        return "Computer Wins!"

st.header("Choose your weapon:")
col1, col2, col3 = st.columns(3)

player_choice = None
if col1.button("Rock"):
    player_choice = "Rock"
if col2.button("Paper"):
    player_choice = "Paper"
if col3.button("Scissors"):
    player_choice = "Scissors"

if player_choice:
    computer_choice = random.choice(["Rock", "Paper", "Scissors"])
    result = determine_winner(player_choice, computer_choice)

    # Update scores
    if "You Win" in result:
        st.session_state.player_score += 1
    elif "Computer Wins" in result:
        st.session_state.computer_score += 1

    # Append new round to history and save it
    st.session_state.history.append({
        "Round": len(st.session_state.history) + 1,
        "Player": player_choice,
        "Computer": computer_choice,
        "Result": result
    })
    save_data(st.session_state.history)

    # Display current round's result
    st.write(f"You chose: **{player_choice}**")
    st.write(f"Computer chose: **{computer_choice}**")
    st.subheader(f"Result: {result}")

#Display Scores and History
st.header("Game Score")
st.write(f"**Player:** {st.session_state.player_score} | **Computer:** {st.session_state.computer_score}")

if st.session_state.history:
    st.header("Game History")
    # Display history in a tabular format using pandas
    history_df = pd.DataFrame(st.session_state.history)
    st.dataframe(history_df)

    # Determine and display the overall winner
    if st.session_state.player_score > st.session_state.computer_score:
        st.success("You are the overall winner so far!")
    elif st.session_state.computer_score > st.session_state.player_score:
        st.error("The computer is the overall winner so far!")
    else:
        st.info("It's a tie overall so far!")

#Option to Reset the Game
if st.button("Reset Game"):
    # Clear the session state
    st.session_state.history = []
    st.session_state.player_score = 0
    st.session_state.computer_score = 0
    st.session_state.initialized = False # Allows re-initialization on rerun
    
    # Clear the JSON file
    save_data([]) 
    
    # Rerun the app to reflect the reset state
    st.rerun()