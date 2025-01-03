import streamlit as st
import pandas as pd
import random
from database import insert_answer, get_words_to_review, get_categories_and_subcategories

############################
# --- Category and Subcategory Selection ---
with st.sidebar:
    st.header("Filtres")
    df_categories = get_categories_and_subcategories()
    selected_categories = st.multiselect("Categories", df_categories['category'].tolist(), key="categories")

    available_subcategories = []
    if selected_categories:
        subcategories_filtered = df_categories[df_categories['category'].isin(selected_categories)]['subcategories'].unique()
        available_subcategories = list(set(', '.join(subcategories_filtered).split(', '))) if subcategories_filtered.size > 0 else []
    selected_subcategories = st.multiselect("Subcategories", available_subcategories, key="subcategories")


user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in to view words to review.")
    st.stop()  # Stop execution if not logged in
    
words_to_review_df = get_words_to_review(user_id, selected_categories, selected_subcategories)
#######################################
mots_francais = words_to_review_df['french_word'].tolist()
mots_russes = words_to_review_df['russian_word'].tolist()
vocabulaire = dict(zip(mots_francais, mots_russes))
word_ids = dict(zip(mots_francais, words_to_review_df['word_id'].tolist()))
#######################################
def on_change_callback():
    """This function will be called when the text input's value changes."""
    st.session_state.is_disabled = False
    word_id = word_ids.get(st.session_state.mot_francais)
    is_correct = st.session_state.input_text == vocabulaire[st.session_state.mot_francais]
    if is_correct:
        st.success('Bien joué!', icon="✅")
    else:
        st.error('À réviser!', icon="🚨")

    st.session_state.answers.append(st.session_state.input_text)
    st.session_state.questions.append(st.session_state.mot_francais)
    user_id = st.session_state.get("user_id")
    if user_id:
        insert_answer(st.session_state.user_id, word_id, is_correct)
    else:
        st.warning("User ID not found. Answer not saved to database.")
    

# Initialize session state
if "mot_francais" not in st.session_state:
    st.session_state.mot_francais = ""
if "mot_russe" not in st.session_state:
    st.session_state.mot_russe = ""
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "answers" not in st.session_state:
    st.session_state.answers = []
if "questions" not in st.session_state:
    st.session_state.questions = []
if 'is_disabled' not in st.session_state:
    st.session_state.is_disabled = False
if 'mot_deja_donnes' not in st.session_state:
    st.session_state.mot_deja_donnes = []

# --- Fonction pour choisir un mot français aléatoire
def choisir_mot():
    if len(st.session_state.mot_deja_donnes) == len(mots_francais):
        st.warning("Tous les mots ont été utilisés !")
        return None  # Or handle this case differently
    
    while True:
        mot_aleatoire = random.choice(mots_francais)
        if mot_aleatoire not in st.session_state.mot_deja_donnes:
            st.session_state.mot_deja_donnes.append(mot_aleatoire)
            return mot_aleatoire

# --- Fonction pour verouiller le bouton nouveau mot tant qu'une réponse n'est pas entrée
def lock_button():
    st.session_state.is_disabled = True

# -- Remaing words
remaining_words = len(mots_francais) - len(st.session_state.mot_deja_donnes)
remaining_words_display = st.empty()  
remaining_words_display.info(f"Words remaining: {remaining_words}")
# Reset button
if st.button("Nouveau mot", type="secondary", icon="💥", disabled = st.session_state.is_disabled, on_click=lock_button):
    st.session_state.mot_francais = choisir_mot()
    st.session_state.input_text = ""
    st.write("Entrez la traduction en allemand (ß):")
    st.write(st.session_state.mot_francais)
    st.text_input("Enter some text:", key="input_text", on_change=on_change_callback)
    

# Create a dataframe from session state data
df_answers = pd.DataFrame({
    "Question (Français)": st.session_state.questions,
    "Réponse de l'utilisateur": st.session_state.answers,
})

# Add a column to indicate correct/incorrect answers
df_answers["Correct ?"] = df_answers["Question (Français)"].apply(lambda x: vocabulaire.get(x)) == df_answers["Réponse de l'utilisateur"]

# Display the dataframe
st.dataframe(df_answers)

if st.button("Nouvelle session", type="primary"):
    st.session_state.answers = []
    st.session_state.questions = []
    st.session_state.mot_deja_donnes = []
    st.session_state.is_disabled = False
    get_words_to_review.clear()
    st.rerun()