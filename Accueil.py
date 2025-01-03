import streamlit as st
from auth import authenticate, create_user
from database import insert_data_into_db
from datavalidation import read_and_validate_csv

st.set_page_config(page_title="Vocabulaire Russe", page_icon=":ru:", layout="centered")
st.set_page_config(layout="centered")

# --- Sidebar with Login/Signup ---
with st.sidebar:
    st.subheader("Authentification")
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.session_state.username = st.text_input("Nom d'utilisateur")
        st.text_input("Mot de passe", type="password", key="password", on_change=authenticate )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Connexion", use_container_width=True):
                if authenticate():
                    st.success("Connecté avec succès!")
                    st.session_state["authenticated"] = True
                    st.rerun()  # Rerun to show authenticated content
                else:
                    st.error("Nom d'utilisateur ou mot de passe incorrect.")
        with col2:
          if st.button("Créer", use_container_width=True):
               create_user(st.session_state.username, st.session_state.password)
    else:
        if 'username' in st.session_state:
            st.write(f"Bienvenue, {st.session_state.username}!")
            st.write(st.session_state["authenticated"])
        if st.button("Déconnexion"):
            st.session_state["authenticated"] = False
            st.rerun()  # Rerun to show login screen

# --- File Upload ---
if st.session_state.authenticated:

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file:
        validated_data = read_and_validate_csv(uploaded_file)
        if validated_data: # Check if validated data is not None
            insert_data_into_db(validated_data)
            st.cache_data.clear()
            st.balloons()

    if st.button('Clear cached data'):
        st.cache_data.clear()
        st.write('Cache cleared!')