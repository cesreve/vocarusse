import streamlit as st
import pandas as pd
import random
from database import insert_answer, get_words_to_review, get_categories_and_subcategories

# --- Fonction pour choisir un mot français aléatoire (modified)
def choisir_mot():
    mots_disponibles = [mot for mot in mots_francais if mot not in st.session_state.mot_deja_vus]
    if not mots_disponibles:
        st.warning("Tous les mots ont été utilisés !")
        return None
    return random.choice(mots_disponibles)
    
# --- Category and Subcategory Selection ---
with st.sidebar:
    st.header("Filtres")
    df_categories = get_categories_and_subcategories()
    # df_categories = ['Verbes', 'Couleur']
    selected_categories = st.multiselect("Categories", df_categories['category'].tolist(), key="categories")
    # selected_categories = st.multiselect("Categories", df_categories, key="categories")
    available_subcategories = []
    if selected_categories:
        subcategories_filtered = df_categories[df_categories['category'].isin(selected_categories)]['subcategories'].unique()
        available_subcategories = list(set(', '.join(subcategories_filtered).split(', '))) if subcategories_filtered.size > 0 else []
        # available_subcategories = ['Top100', 'Couleurs de base']
    selected_subcategories = st.multiselect("Subcategories", available_subcategories, key="subcategories")

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in to view words to review.")
    st.stop()

words_to_review_df = get_words_to_review(user_id, selected_categories, selected_subcategories)
# words_to_review_df = pd.read_csv('data3.csv')
#######################################
mots_francais = words_to_review_df['french_word'].tolist()
mots_russes = words_to_review_df['russian_word'].tolist()
vocabulaire = dict(zip(mots_francais, mots_russes))
word_ids = dict(zip(mots_francais, words_to_review_df['word_id'].tolist()))

# st.write(vocabulaire)
# st.write(mots_francais)
# Modified callback functions
def i_know_callback():
    word_id = word_ids.get(st.session_state.mot_francais)
    insert_answer(st.session_state.user_id, word_id, True)  # Correct answer
    st.session_state.mot_deja_vus.append(st.session_state.mot_francais)
    st.session_state.mot_francais = choisir_mot()  # Get the next word
    st.success('Bien joué!', icon="✅")

def i_dont_know_callback():
    word_id = word_ids.get(st.session_state.mot_francais)
    insert_answer(st.session_state.user_id, word_id, False)  # Incorrect answer
    st.session_state.mot_francais = choisir_mot()  # Get the next word
    st.error('À réviser!', icon="🚨")

# Initialize/modify session state
if 'mot_deja_vus' not in st.session_state:
    st.session_state.mot_deja_vus = [] # Words already seen in the current session
if "mot_francais" not in st.session_state:
    st.session_state.mot_francais = choisir_mot() # Initialize with a word

# ... (other session state initializations can be removed)
# Display the current word
if st.session_state.mot_francais:  # Check if there's a word to display
    st.write(st.session_state.mot_francais)
    #st.write(vocabulaire[st.session_state.mot_francais]) #["mot_francais"])

    col1, col2 = st.columns(2)  # Arrange buttons in columns
    with col1:
        st.button("I know this word", on_click=i_know_callback)
    with col2:
        st.button("I don't know this word", on_click=i_dont_know_callback)


# ... (Remove the text input and related code)

# ... (The "Nouvelle session" button and its functionality remains unchanged)

# The dataframe to display answers is no longer relevant in this version, so remove it.

if st.button("Nouvelle session", type="primary"):
    st.session_state.answers = []
    st.session_state.questions = []
    st.session_state.mot_deja_donnes = []
    st.session_state.is_disabled = False
    get_words_to_review.clear()
    st.rerun()