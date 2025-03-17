import streamlit as st
import pandas as pd
import wikipedia

# Configuration générale de la page (on élargit pour plus de lisibilité)
st.set_page_config(page_title="Spotify Data Explorer", layout="wide")

# Petit style CSS pour améliorer l'affichage (rien de trop fancy)
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #f0f2f6; padding: 20px; }
        .stTitle { color: #1DB954; font-size: 40px; font-weight: bold; }
        div.stButton > button:first-child { background-color: #1DB954; color: white; font-size: 18px; border-radius: 10px; }
        div.stButton > button:hover { background-color: #14833b; color: white; }
        .main { background-color: #f7f7f7; }
    </style>
""", unsafe_allow_html=True)

# Chargement des données (mise en cache pour éviter de recharger à chaque exécution)
@st.cache_data
def load_data():
    df_artists = pd.read_csv("data/artists.csv", encoding="utf-8")
    df_track = pd.read_csv("data/tracks.csv", encoding="utf-8")
    df_top200 = pd.read_csv("data/spotify_top200_global.csv", encoding="utf-8")

    # Nettoyage rapide des colonnes
    df_artists.rename(columns={'name': 'artists'}, inplace=True)
    df_artists["artists"] = df_artists["artists"].str.lower()
    df_artists["genres"] = df_artists["genres"].fillna("").astype(str)

    # Nettoyage des caractères inutiles dans df_track
    df_track.replace(to_replace=r'\[|\]', value='', regex=True, inplace=True)
    df_track.replace(to_replace="'", value='', regex=True, inplace=True)

    # Conversion des dates (gestion des erreurs incluse)
    df_track["release_date"] = pd.to_datetime(df_track["release_date"], errors="coerce")
    df_track["release_year"] = df_track["release_date"].dt.year.astype("Int64")

    # Nombre de singles par artiste dans le top 200
    singleparartiste = df_top200.groupby("Artist")["Title"].nunique().reset_index()
    singleparartiste.columns = ["Artist", "Nombre de single dans le top200"]

    return df_artists, df_track, df_top200, singleparartiste

df_artists, df_track, df_top200, singleparartiste = load_data()

# Fonction pour récupérer la page Wikipédia d'un artiste
def get_wikipedia_link(artist_name):
    try:
        return wikipedia.page(artist_name).url
    except wikipedia.exceptions.DisambiguationError:
        return f"https://en.wikipedia.org/wiki/{artist_name.replace(' ', '_')}"
    except wikipedia.exceptions.PageError:
        return None

# Recherche d'un artiste (followers, chansons populaires, lien Wikipedia...)
def rechercher_nom(nom):
    artiste = df_artists[df_artists['artists'].str.lower() == nom.lower()]
    if artiste.empty:
        return None, None, None, None, None  
    
    nb_abos = artiste['followers'].values[0]
    morceaux = df_track[df_track['artists'].str.contains(nom, case=False, na=False)]

    if not morceaux.empty:
        morceaux["release_year"] = morceaux["release_year"].astype("Int64")

    pop = morceaux.nlargest(3, 'popularity')[['name', 'popularity']] if not morceaux.empty else None
    recence = morceaux.nlargest(3, 'release_year')[['name', 'release_year']] if not morceaux.empty else None
    artiste_data = singleparartiste[singleparartiste['Artist'].str.lower() == nom.lower()]
    nb_chansons = artiste_data["Nombre de single dans le top200"].values[0] if not artiste_data.empty else 0

    wikipedia_link = get_wikipedia_link(nom)

    return nb_abos, pop, recence, nb_chansons, wikipedia_link

# Recherche d'un titre musical
def recherche_titre(titre):
    titres_trouves = df_track[df_track['name'].str.contains(titre, case=False, na=False)]
    if titres_trouves.empty:
        return None
    return titres_trouves.sort_values(by='popularity', ascending=False).head(20)

# **Début de l'application Streamlit**
st.image("https://upload.wikimedia.org/wikipedia/commons/2/26/Spotify_logo_with_text.svg", width=250)
st.title("Spotify Data Explorer")

# Ajout de la sidebar
st.sidebar.header("Recherches & Filtres")
page_selection = st.sidebar.radio("Choisissez une option :", ["Recherche d'un artiste", "Recherche d'un titre"])

# Recherche d'un artiste
if page_selection == "Recherche d'un artiste":
    st.sidebar.subheader("Recherche d'un artiste")
    artiste_nom = st.sidebar.text_input("Entrez le nom d'un artiste :")

    if st.sidebar.button("Rechercher"):
        if artiste_nom:
            nb_followers, pop_songs, recent_songs, nb_top200, wiki_link = rechercher_nom(artiste_nom)
            if nb_followers is not None:
                st.subheader(f"Artiste : {artiste_nom.title()}")
                st.write(f"Nombre de followers : {nb_followers}")
                st.write(f"Nombre de chansons dans le Top 200 Global 2020 : {nb_top200}")

                if wiki_link:
                    st.markdown(f"[Page Wikipédia de {artiste_nom}]({wiki_link})")

                if pop_songs is not None:
                    st.write("Chansons les plus populaires :")
                    st.dataframe(pop_songs)
                if recent_songs is not None:
                    st.write("Chansons les plus récentes :")
                    st.dataframe(recent_songs)
            else:
                st.warning("Artiste non trouvé.")

# Recherche par titre
if page_selection == "Recherche d'un titre":
    st.sidebar.subheader("Recherche par titre")
    titre = st.sidebar.text_input("Entrez un titre de chanson :")

    if st.sidebar.button("Rechercher titre"):
        if titre:
            resultats = recherche_titre(titre)
            if resultats is not None:
                st.subheader(f"Résultats pour : {titre.title()}")
                st.dataframe(resultats[['name', 'artists', 'popularity']])
            else:
                st.warning("Aucun résultat trouvé.")
