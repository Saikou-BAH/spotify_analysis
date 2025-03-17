import streamlit as st
import pandas as pd

# Chargement des données (cache pour éviter de recharger à chaque exécution)
@st.cache_data
def load_data():
    df_artists = pd.read_csv("data/artists.csv", encoding="utf-8")
    df_track = pd.read_csv("data/tracks.csv", encoding="utf-8")

    # Renommage et nettoyage des colonnes
    df_artists.rename(columns={'name': 'artists'}, inplace=True)
    df_artists["artists"] = df_artists["artists"].str.lower()
    df_artists["genres"] = df_artists["genres"].fillna("").astype(str)

    # Nettoyage des caractères inutiles
    df_track.replace(to_replace=r'\[|\]', value='', regex=True, inplace=True)
    df_track.replace(to_replace="'", value='', regex=True, inplace=True)

    # Transformation de la date de sortie en datetime
    df_track["release_date"] = pd.to_datetime(df_track["release_date"], errors="coerce")
    df_track["release_year"] = df_track["release_date"].dt.year.astype("Int64").astype(str)

    return df_artists, df_track

df_artists, df_track = load_data()

# Fonction pour récupérer les chansons d'une année et d'un genre donné
def lookby_year_genre(year, genre):
    """ Recherche des chansons par année et genre, triées par popularité """

    if not isinstance(year, str) or not isinstance(genre, str) or not year.strip() or not genre.strip():
        st.error("Veuillez entrer une année et un genre valides.")
        return pd.DataFrame()

    if "popularity" not in df_track.columns:
        st.error("Erreur : La colonne 'popularity' est introuvable.")
        return pd.DataFrame()

    # Sélection des colonnes pertinentes
    tab_art = df_artists[['id', 'genres']].copy()
    tab_track = df_track[['name', 'popularity', 'id_artists', 'release_year', 'artists']].copy()

    if tab_art.empty or tab_track.empty:
        st.warning("Données manquantes, impossible de fusionner les tables.")
        return pd.DataFrame()

    # Fusion des tables sur les IDs artistes
    tab_at = tab_art.merge(tab_track, left_on='id', right_on='id_artists', how='left')

    if "popularity" not in tab_at.columns:
        st.error("Erreur après fusion : colonne 'popularity' introuvable.")
        return pd.DataFrame()

    # Filtrage des résultats par année et genre
    mask_year = tab_at['release_year'] == year
    mask_genre = tab_at['genres'].str.contains(genre, case=False, na=False)
    tab_at_yg = tab_at[mask_year & mask_genre]

    if tab_at_yg.empty:
        st.warning(f"Aucun résultat trouvé pour {year} dans le genre {genre}.")
        return pd.DataFrame()

    # Tri des résultats par popularité et artiste
    return tab_at_yg[['name', 'popularity', 'artists']].sort_values(by=['popularity', 'artists'], ascending=[False, True])

# Interface Streamlit
st.title("Spotify Data Explorer")

st.header("Filtrage par année et genre")
annee = st.text_input("Entrez une année :")
genre = st.text_input("Entrez un genre musical :")

if st.button("Filtrer"):
    if annee and genre:
        resultats = lookby_year_genre(annee, genre)
        if not resultats.empty:
            st.dataframe(resultats)
        else:
            st.warning("Aucun résultat pour ces critères.")
