from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .ORM import Client, Transporteur, Commande, Ville, Base
import os
from dotenv import load_dotenv
from pathlib import Path


from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

# from datetime import datetime

load_dotenv(Path(".env"))

host = os.getenv("MYSQL_HOST", "127.0.0.1")
user = os.getenv("MYSQL_USER")
pwd = os.getenv("MYSQL_PASSWORD")
db = os.getenv("MYSQL_DATABASE")
port = os.getenv("MYSQL_PORT", 3306)


def get_mysql_engine():
    return create_engine(f"mysql+mysqlconnector://{user}:{pwd}@{host}:{port}/{db}")


def check_connection(engine):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as e:
        raise ConnectionError("Impossible de se connecter à la base.") from e


def clean_db(engine):
    # Creation de l'architecture de la db
    try:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
    except Exception as e:
        print(f"Erreur lors de la creation de la db:{str(e)}")


def check_datas(df):
    try:
        
        required_columns = [
            "commande_id",
            "client_id",
            "ville_livraison",
            "date_commande",
            "date_livraison_prevue",
            "date_livraison_reelle",
            "poids_kg",
            "transporteur",
            "distance_km",
            "nb_articles",
            "statut",
            "nb_jour_retard",
            "niveau_retard",
        ]



        # check colonne manqute
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Colonnes manquantes : {missing}")

        if df[required_columns].isnull().any().any():
            raise ValueError("Le CSV contient des valeurs obligatoires manquantes.")
        
        if df["commande_id"].duplicated().any():
            raise ValueError("commande_id dupliqué dans le CSV")
        
        # check type
        df["poids_kg"] = pd.to_numeric(df["poids_kg"], errors="raise")
        df["distance_km"] = pd.to_numeric(df["distance_km"], errors="raise")
        df["nb_articles"] = pd.to_numeric(df["nb_articles"], errors="raise").astype(int)
        df["nb_jour_retard"] = pd.to_numeric(df["nb_jour_retard"], errors="raise")

        df["date_commande"] = pd.to_datetime(df["date_commande"], errors="raise")
        df["date_livraison_prevue"] = pd.to_datetime(df["date_livraison_prevue"], errors="raise")
        df["date_livraison_reelle"] = pd.to_datetime(df["date_livraison_reelle"], errors="raise")
        
        
        return df
    except Exception as e:
        raise


def ingestion(df):
    try:

        lstClient = dict()
        lstTransporteur = dict()
        lstCommandes = []
        lstVilles = dict()

        for row in df.itertuples(index=False):

            # Ville
            nameVille = row.ville_livraison
            ville = lstVilles.get(nameVille)
            if ville == None:
                ville = Ville(idVille=len(lstVilles) + 1, name=nameVille)
                lstVilles[nameVille] = ville

            # Transporteur
            nameTramps = row.transporteur
            transporteur = lstTransporteur.get(nameTramps)
            if transporteur == None:
                transporteur = Transporteur(
                    idTransporteur=len(lstTransporteur) + 1, name=nameTramps
                )
                lstTransporteur[nameTramps] = transporteur

            # Client
            idClient = row.client_id
            client = lstClient.get(idClient)
            if client == None:
                client = Client(idClient=idClient, idVille=ville.idVille)
                lstClient[idClient] = client

            # Commandes
            commande = Commande(
                idCommande=row.commande_id,
                idClient=client.idClient,
                idTransporteur=transporteur.idTransporteur,
                dateCommande=row.date_commande,
                datePrevue=row.date_livraison_prevue,
                dateReelle=row.date_livraison_reelle,
                poidsKg=row.poids_kg,
                distanceKm=row.distance_km,
                nbArticle=row.nb_articles,
                statut=row.statut,
                jourRetard=row.nb_jour_retard,
                niveauRetard=row.niveau_retard,
            )
            lstCommandes.append(commande)

        return lstCommandes, lstClient, lstTransporteur, lstVilles
    except Exception as e:
        raise


def add_lstVilles(lstVilles, session):
    try:
        session.add_all(lstVilles.values())
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    except SQLAlchemyError:
        session.rollback()
        raise


def add_lstClient(lstClient, session):
    try:
        session.add_all(lstClient.values())
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    except SQLAlchemyError:
        session.rollback()
        raise


def add_lstTransporteur(lstTransporteur, session):
    try:
        session.add_all(lstTransporteur.values())
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    except SQLAlchemyError:
        session.rollback()
        raise



def add_lstCommandes(lstCommandes, session):
    try:
        session.add_all(lstCommandes)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    except SQLAlchemyError:
        session.rollback()
        raise



if __name__ == "__main__":

    engine = get_mysql_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    check_connection(engine)
    clean_db(engine)
    
    df = pd.read_csv("./datas/commandes_clean.csv")
    df = check_datas(df)

    lstCommandes, lstClient, lstTransporteur, lstVilles = ingestion(df)

    add_lstVilles(lstVilles, session)
    add_lstClient(lstClient, session)
    add_lstTransporteur(lstTransporteur, session)
    add_lstCommandes(lstCommandes, session)
