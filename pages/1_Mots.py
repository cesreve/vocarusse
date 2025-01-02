import streamlit as st
from gtts import gTTS
import base64
from io import BytesIO
from database import get_words, get_categories_and_subcategories

##################################
# st.set_page_config(page_title="Vocabulaire Russe", page_icon=":ru:", layout="centered")

##################################
# --- Helper Function for TTS ---
def get_audio_base64(text):
    tts = gTTS(text=text, lang='ru') 
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    b64 = base64.b64encode(fp.read()).decode()
    return f'<audio controls src="data:audio/mpeg;base64,{b64}"/>'

# --- Streamlit App ---
# st.title(':flag-fr: Français-Russe :flag-ru:')

st.write("Sélectionner au moins une catégorie ou sous-catégorie.")

if 'username' in st.session_state:
    if len(st.session_state.username)>0:
        st.write(f"Vous êtes authenthifié en tant que {st.session_state.username}!")  

# --- Sidebar ---
with st.sidebar:
    st.header("Filtres")
    df_categories = get_categories_and_subcategories()
    selected_categories = st.multiselect("Categories", df_categories['category'].tolist(), key="categories")

    available_subcategories = []
    if selected_categories:
        subcategories_filtered = df_categories[df_categories['category'].isin(selected_categories)]['subcategories'].unique()
        available_subcategories = list(set(', '.join(subcategories_filtered).split(', '))) if subcategories_filtered.size > 0 else []
    selected_subcategories = st.multiselect("Subcategories", available_subcategories, key="subcategories")

# Load and Filter Data
if selected_categories and selected_subcategories:
    filtered_df = get_words(selected_categories, selected_subcategories)

else:
    st.stop()
# --- Rename columns ---
filtered_df = filtered_df.rename(columns={
    'category': 'Catégorie',
    'subcategory': 'Sous-catégorie',
    'french_word': 'Français',
    'russian_word': 'Russe',
    'example_sentence': 'Exemple'
})

# --- Add TTS Column ---
filtered_df.loc[:, 'Écouter'] = filtered_df['Russe'].apply(get_audio_base64)

# --- Display DataFrame with HTML for Audio ---
if not filtered_df.empty:
    filtered_df = filtered_df.sample(frac=1).reset_index(drop=True)
    st.write(
        filtered_df[['Français', 'Russe', 'Écouter', 'Exemple']].to_html(
            escape=False, formatters={"Écouter": lambda x: x}, index=False
        ),
        unsafe_allow_html=True,
    )