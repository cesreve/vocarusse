import psycopg2
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List
from datavalidation import Word
import sqlalchemy

# Get the database URL from environment variable
DATABASE_URL = st.secrets["my_database"]["DATABASE_URL"]

# --- connect_to_db
def connect_to_db():
    """Connects to PostgreSQL, creates a table, and queries it."""
    conn = None
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

# --- insert_answer
def insert_answer(user_id, word_id, is_correct):  # Add word_id as a parameter
    """Inserts the user's answer into the database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        # Insert the answer data.
        insert_query = """
            INSERT INTO russian.answers (user_id, word_id, is_correct, answer_date)
            VALUES (%s, %s, %s, %s);
        """
        cur.execute(insert_query, (user_id, word_id, is_correct, datetime.now()))  # Pass word_id

        conn.commit()
        cur.close()
        conn.close()

    except psycopg2.Error as e:
        st.error(f"Database error: {e}")

# --- fetch_answers_from_db
def fetch_answers_from_db(user_id):
    """Récupère les réponses de l'utilisateur depuis la base de données."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT russian_word, answer_date, is_correct
            FROM (
                SELECT 
                    russian_word, 
                    answer_date, 
                    is_correct,
                    RANK() OVER (PARTITION BY russian_word ORDER BY answer_date DESC) as rank_number
                FROM russian.answers
                WHERE user_id = %s
            ) AS ranked_answers
            WHERE 1=1
                AND rank_number = 1
                AND is_correct;
                    """, (user_id,))
        answers_data = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        df_answers = pd.DataFrame(answers_data, columns=columns)
        cur.close()
        conn.close()
        return df_answers
    except psycopg2.Error as e:
        st.error(f"Erreur de base de données: {e}")
        return None


# --- get_categories_and_subcategories
@st.cache_data  # Cache the result for performance
def get_categories_and_subcategories():
    """Fetches categories and their subcategories from the database and stores them in session state."""
    with st.spinner('Chargement des catégories...'):
        try:
            engine = sqlalchemy.create_engine(DATABASE_URL)
            query = """
                SELECT category, string_agg(DISTINCT subcategory, ', ') AS subcategories
                FROM russian.words
                GROUP BY category;
            """
            df_categories = pd.read_sql_query(query, engine)  # Use pandas for easy DataFrame creation
            st.session_state.categories_df = df_categories  # Store in session state
            return df_categories # return for usage if required

        except psycopg2.Error as e:
            st.error(f"Database error: {e}")
            return None  # Return None to indicate an error

# --- Get all words based on category and subcategory
@st.cache_data
def get_words(selected_categories=None, selected_subcategories=None): 
    """Retrieves words based on the filters."""
    with st.spinner('Chargement des mots...'):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            query = """
                SELECT w.word_id, w.french_word, w.russian_word, w.category, w.subcategory, w.example_sentence
                FROM russian.words w
                WHERE 1=1
            """
            params = []

            if selected_categories:
                query += " AND w.category IN %s"
                params.append(tuple(selected_categories))

            if selected_subcategories:
                query += " AND w.subcategory IN %s"
                params.append(tuple(selected_subcategories))

            query += ";"

            cur.execute(query, params)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            df_to_review = pd.DataFrame(rows, columns=columns)
            conn.close()
            return df_to_review

        except psycopg2.Error as e:
            st.error(f"Database error: {e}")
            return None
    
# --- Get words to review
@st.cache_data
def get_words_to_review(user_id, selected_categories=None, selected_subcategories=None):
    """Retrieves words the user needs to review, filtering by category and subcategory."""
    with st.spinner('Chargement des mots à réviser...'):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            query = """
                SELECT 
                    w.word_id, 
                    w.french_word, 
                    w.russian_word, 
                    w.category, 
                    w.subcategory
                FROM 
                    russian.words w
                LEFT JOIN 
                    russian.user_word_learning uwl ON w.word_id = uwl.word_id AND uwl.user_id = %s
                WHERE 1=1
                    AND CASE
                        -- mot pas encore vu    s
                        WHEN uwl.derniere_date_mise_a_jour IS NULL THEN TRUE 
                        -- conditions sur le commpteur
                        WHEN uwl.compteur = 0 THEN TRUE
                        WHEN uwl.compteur = 1 AND uwl.derniere_date_mise_a_jour < NOW() - 1 * INTERVAL '1 day' THEN TRUE
                        WHEN uwl.compteur = 2 AND uwl.derniere_date_mise_a_jour < NOW() - 3 * INTERVAL '1 day' THEN TRUE
                        WHEN uwl.compteur = 3 AND uwl.derniere_date_mise_a_jour < NOW() - 6 * INTERVAL '1 day' THEN TRUE
                        WHEN uwl.compteur = 4 AND uwl.derniere_date_mise_a_jour < NOW() - 15 * INTERVAL '1 day' THEN TRUE
                        WHEN uwl.compteur = 5 AND uwl.derniere_date_mise_a_jour < NOW() - 30 * INTERVAL '1 day' THEN TRUE
                        ELSE FALSE
                    END
        """
            
            params = [user_id]

            if selected_categories:
                query += " AND w.category IN %s"
                params.append(tuple(selected_categories))

            if selected_subcategories:
                query += " AND w.subcategory IN %s"
                params.append(tuple(selected_subcategories))

            query += ";"

            cur.execute(query, params)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            df_to_review = pd.DataFrame(rows, columns=columns)
            conn.close()
            return df_to_review

        except psycopg2.Error as e:
            st.error(f"Database error: {e}")
            return None

# --- Function to insert data, checking for duplicates
def insert_data_into_db(data: List[Word]):
    """Inserts data, checking for duplicates based on the russian word."""
    if data is None:
        return

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    try: 
        for word in data:
            try:
                # Check for duplicates (using russian word)
                check_query = "SELECT 1 FROM russian.words WHERE russian_word = %s"
                cursor.execute(check_query, (word.russian_word,))
                exists = cursor.fetchone()

                if not exists:
                    insert_query = """
                        INSERT INTO russian.words (french_word, russian_word, category, subcategory, example_sentence)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (word.french_word, word.russian_word, word.category, word.subcategory, word.example_sentence))
                    st.success(f"Inserted: {word.russian_word}") # Feedback inside the loop
                else:
                    st.warning(f"Skipped (duplicate russian word): {word.russian_word}") # Inside loop

            except psycopg2.Error as e:
                st.error(f"Database error inserting word {word.russian_word}: {e}")
                conn.rollback()  # Rollback for individual word insertion errors

        conn.commit()  # Commit outside the loop after all insertions
    except psycopg2.Error as e:
        st.error(f"Overall database error: {e}")
        conn.rollback()

    finally: # finally outside loop
        cursor.close()
        conn.close()