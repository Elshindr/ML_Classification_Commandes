import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ingestion.ORM import Client, Transporteur, Commande, Ville, Base
from ingestion.ingest import (
    check_datas,
    ingestion,
    add_lstVilles,
    add_lstClient,
    add_lstTransporteur,
    add_lstCommandes,
    check_connection
)
from sqlalchemy.exc import IntegrityError
import datetime


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()

def test_mauvaise_connexion():

    engine = create_engine(
        "mysql+mysqlconnector://bad:bad@localhost:9999/test"
    )
    with pytest.raises(ConnectionError):
        check_connection(engine)

def test_insertion_valide(session):
    df = pd.DataFrame(
        [
            {
                "commande_id": "CMD-10234",
                "client_id": "CLI-5521",
                "ville_livraison": "Lyon",
                "date_commande": "2024-12-28 17:42:49",
                "date_livraison_prevue": "2025-12-02 14:51",
                "date_livraison_reelle": "2026-07-02 10:01:44",
                "poids_kg": 2.3,
                "transporteur": "ColisExpress",
                "distance_km": 14.5,
                "nb_articles": 3,
                "statut": "livre",
                "nb_jour_retard": 12,
                "niveau_retard": "Léger",
            }
        ]
    )
    df = check_datas(df)
    lstCommandes, lstClient, lstTransporteur, lstVilles = ingestion(df)

    add_lstVilles(lstVilles, session)
    add_lstClient(lstClient, session)
    add_lstTransporteur(lstTransporteur, session)
    add_lstCommandes(lstCommandes, session)

    ville__ = lstVilles.get("Lyon")
    assert ville__.idVille == 1
    assert ville__.name == "Lyon"

    assert session.query(Ville).count() == 1
    assert session.query(Transporteur).count() == 1
    assert session.query(Client).count() == 1

    ville = session.query(Ville).first()
    assert ville.idVille == 1
    assert ville.name == "Lyon"

    client = session.query(Client).first()
    assert client.idVille == 1
    assert client.idClient == "CLI-5521"

    trps = session.query(Transporteur).first()
    assert trps.idTransporteur == 1
    assert trps.name == "ColisExpress"

    cmd = session.query(Commande).first()
    assert cmd.idCommande == "CMD-10234"
    assert client.idClient == "CLI-5521"
    assert cmd.idTransporteur == 1
    assert isinstance(cmd.dateCommande, datetime.datetime)
    assert isinstance(cmd.nbArticle, int)
    assert isinstance(cmd.distanceKm, float)


def test_colonne_manquante():

    df = pd.DataFrame([{"commande_id": "CMD-001", "client_id": "CLI-001"}])
    with pytest.raises(ValueError):
        check_datas(df)

def test_champ_obligatoire_vide():
    df = pd.DataFrame([
        {
            "commande_id": None,
            "client_id": "CLI-001",
            "ville_livraison": "Paris"
        }
    ])

    with pytest.raises(ValueError):
        check_datas(df)
        
def test_poids_mauvais_type():
        df = pd.DataFrame([
            {
                "commande_id": "CMD-001",
                "client_id": "CLI-001",
                "ville_livraison": "Paris",
                "date_commande": "2025-01-01",
                "date_livraison_prevue": "2025-01-02",
                "date_livraison_reelle": "2025-01-03",
                "poids_kg": "ABC",
                "transporteur": "DHL",
                "distance_km": 20,
                "nb_articles": 2,
                "statut": "livre",
                "nb_jour_retard": 0,
                "niveau_retard": "aucun"
            }
        ])

        with pytest.raises(Exception):
            check_datas(df)
            



def test_commande_duplicate(session):

    commande = Commande(
        idCommande="CMD-001",
        idClient="CLI-001",
        idTransporteur=1,
        dateCommande=pd.to_datetime("2025-01-01"),
        datePrevue=pd.to_datetime("2025-01-02"),
        dateReelle=pd.to_datetime("2025-01-03"),
        poidsKg=5,
        distanceKm=10,
        nbArticle=1,
        statut="livre",
        jourRetard=0,
        niveauRetard="aucun"
    )
    session.add(commande)
    session.commit()


    duplicate = Commande(
        idCommande="CMD-001",
        idClient="CLI-001",
        idTransporteur=1,
        dateCommande=pd.to_datetime("2026-02-21 01:17:26"),
        datePrevue=pd.to_datetime("2026-02-21 01:17:26"),
        dateReelle=pd.to_datetime("2026-02-21 01:17:26"),
        poidsKg=5,
        distanceKm=10,
        nbArticle=1,
        statut="livre",
        jourRetard=0,
        niveauRetard="aucun"
    )
    session.add(duplicate)


    with pytest.raises(IntegrityError):
        session.commit()