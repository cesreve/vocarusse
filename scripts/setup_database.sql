-- Création de la table des utilisateurs
CREATE TABLE IF NOT EXISTS russian.users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Création de la table des mots
CREATE TABLE IF NOT EXISTS russian.words (
    word_id SERIAL PRIMARY KEY,
    french_word TEXT,
    russian_word TEXT,
    category TEXT,
    subcategory TEXT,
    example_sentence TEXT
);
    
-- Création de la table des réponses
CREATE TABLE IF NOT EXISTS russian.answers (
    answer_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    word_id INT NOT NULL,
    is_correct BOOLEAN,
    answer_date TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
    FOREIGN KEY (user_id) REFERENCES users(user_id),  -- Assuming 'users' table exists
    FOREIGN KEY (word_id) REFERENCES words(word_id) -- Assuming 'words' table exists
);

-- Création de la table de répétition espacée
CREATE TABLE IF NOT EXISTS russian.user_word_learning (
    user_id INT NOT NULL,
    word_id INT NOT NULL,
    compteur INT DEFAULT 1,
    derniere_date_mise_a_jour TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, word_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (word_id) REFERENCES words(word_id)
);

-- Fonction pour mettre à jour la table user_learning
CREATE OR REPLACE FUNCTION update_user_word_learning()
RETURNS TRIGGER AS $$
BEGIN
    -- Vérifier si la réponse est correcte
    IF NEW.is_correct THEN
    -- Si la réponse est correcte, incrémenter le compteur
    UPDATE user_word_learning
    SET compteur = compteur + 1,
        derniere_date_mise_a_jour = NOW()
    WHERE user_id = NEW.user_id AND word_id = NEW.word_id;

    -- Si aucune ligne correspondante n'existe, en insérer une nouvelle
    IF NOT FOUND THEN
        INSERT INTO user_word_learning (user_id, word_id, compteur, derniere_date_mise_a_jour)
        VALUES (NEW.user_id, NEW.word_id, 1, NOW());
    END IF;
    ELSE
    -- Si la réponse est incorrecte, réinitialiser le compteur à 0
    UPDATE user_word_learning
    SET compteur = 0,
        derniere_date_mise_a_jour = NOW()
    WHERE user_id = NEW.user_id AND word_id = NEW.word_id;

    -- Si aucune ligne correspondante n'existe, en insérer une nouvelle
    IF NOT FOUND THEN
        INSERT INTO user_word_learning (user_id, word_id, compteur, derniere_date_mise_a_jour)
        VALUES (NEW.user_id, NEW.word_id, 0, NOW());
    END IF;
END IF;

RETURN NEW;

END;
$$ LANGUAGE plpgsql;

-- Create tigger for updateing the user_word_learning function
CREATE TRIGGER update_user_word_learning_trigger
AFTER INSERT ON answers
FOR EACH ROW
EXECUTE PROCEDURE update_user_word_learning();