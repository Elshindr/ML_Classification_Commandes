import pandas as pd
import numpy as np
import json
from datetime import datetime


def set_cat_statut(statut):
    if statut == "livre":
        return 1
    elif statut=="en_cours":
        return 0
    else:
        return -1
def set_niveau(retard):
    if retard < 2:
        return "A l'heure"
    elif retard >= 2 and retard <= 4:
        return "Léger"
    else:
        return "Important"

if __name__ == "__main__":
    df_raw = pd.read_json("./datas/commandes_raw.json")
    df_raw.info()
    # Conversion des types datetime
    df_raw["date_commande"] = df_raw.date_commande.apply(lambda d: pd.to_datetime(d))
    df_raw["date_livraison_prevue"] = df_raw.date_livraison_prevue.apply(lambda d: pd.to_datetime(d))
    df_raw["date_livraison_reelle"] = df_raw.date_livraison_reelle.apply(lambda d: pd.to_datetime(d))

    df_raw.info()
    ## duplicated garde le premier
    df_raw = df_raw.drop_duplicates(subset=["commande_id", "client_id", "date_commande"])
    df_raw = df_raw.drop_duplicates(subset=["commande_id"])
    #print(f"nombre de duplicate: {df_raw.duplicated().sum()}")

    # valeur manquantes
    # on ne garde pas les lignes avec  qui sont à  none
    # on ne peut pas simuler une fause date ou une fauses ville
    df_raw = df_raw.dropna(subset=["date_livraison_reelle","date_livraison_prevue","transporteur","ville_livraison", "client_id","commande_id"])


    #outliers poids , distance, nb_article
    poids_outliers = (df_raw["poids_kg"] > 1000) | (df_raw["poids_kg"] < 0)
    moyenne_valide = df_raw.loc[~poids_outliers, "poids_kg"].mean()
    df_raw.loc[poids_outliers, 'poids_kg'] = moyenne_valide

    nbarct_outliers = (df_raw["nb_articles"] > 2000) 
    moyenne_valide = df_raw.loc[~nbarct_outliers, "nb_articles"].mean()
    df_raw.loc[nbarct_outliers, 'nb_articles'] = round(moyenne_valide)
    #print(f"valeur manquantes par colonnes:\n{df_raw.isna().sum(axis=0)}")

    dst_outliers = (df_raw["distance_km"] > 2000)  | (df_raw["distance_km"] < 0)
    moyenne_valide = df_raw.loc[~dst_outliers, "distance_km"].mean()
    df_raw.loc[dst_outliers, 'distance_km'] = moyenne_valide

    # Val Categorielle
    # status
    #df_raw['statut_cat'] = df_raw.statut.apply(lambda v : set_cat_statut(v))
    #df_raw['transporteur'] = df_raw.transporteur.apply(lambda v : set_cat_transporteur(v))
    #df_raw['statut_cat'] = df_raw.statut.apply(lambda v : set_cat_statut(v))

df_raw["nb_jour_retard"]= (pd.to_datetime(df_raw.date_livraison_reelle) - pd.to_datetime(df_raw.date_livraison_prevue) ).dt.days

df_raw["niveau_retard"] = df_raw["nb_jour_retard"].apply(lambda v: set_niveau(v))

df_raw.to_csv('./datas/commandes_clean.csv', sep=",")