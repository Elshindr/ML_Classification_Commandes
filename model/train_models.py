import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.preprocessing import OrdinalEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report
import joblib
import os
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ingestion.ORM import Client, Transporteur, Commande, Ville, Base
from sqlalchemy import select, text
from sklearn.metrics import accuracy_score 

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


def get_datas_from_db(session):
    # textual_sql=text("SELECT idCommande, idClient, idTransporteur, poidsKg, distanceKm, nbArticle, statut, jourRetard, niveauRetard FROM commande ")
    # orm_sql = select(User).from_statement(textual_sql)
    stm = select(Commande, Client.idVille).join(Commande.rel_idClient_commande)
    # result = session.execute(stm)
    df_cmd = pd.read_sql(stm, session.bind)

    df_ville = pd.read_sql(select(Ville), session.bind)
    df_tspt = pd.read_sql(select(Transporteur), session.bind)
    print(df_cmd)
    return df_cmd, df_ville, df_tspt


def train_model(df):
    y = df.niveauRetard
    X = df[["idTransporteur", "poidsKg", "distanceKm", "nbArticle", "statut"]]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42,stratify=y
    )

    # normaliser les cols num
    cols_num = ["poidsKg", "distanceKm", "nbArticle"]
    sc = StandardScaler()
    # X_train[cols_num] = sc.fit_transform(X_train[cols_num])
    # X_test[cols_num] = sc.transform(X_test[cols_num])
    X_train_num = sc.fit_transform(X_train[cols_num])
    X_test_num = sc.transform(X_test[cols_num])

    # onehotencoder categories
    cols_cat = ["idTransporteur", "statut"]
    enh = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    X_train_cat = enh.fit_transform(X_train[cols_cat])
    X_test_cat = enh.transform(X_test[cols_cat])
    cat_names = enh.get_feature_names_out(cols_cat)
    print(cat_names)

    # df final pour le model
    X_train_final = np.concatenate([X_train_num, X_train_cat], axis=1)
    X_test_final = np.concatenate([X_test_num, X_test_cat], axis=1)
    
    # Encodage target
    encoder_y = LabelEncoder()
    y_encoded = encoder_y.fit_transform(y)
  
    print(dict(enumerate(encoder_y.classes_)))
    # Entrainement
    model= LogisticRegression()
    model.fit(X_train_final, y_train)
    y_pred = model.predict(X_test_final)
    print( classification_report( y_test, y_pred )) 
    print(accuracy_score(y_test, y_pred) )
    print(pd.crosstab(y_test, y_pred, rownames=['Realité'], colnames=['Prédiction']))
    joblib.dump(model, './model/classification_model.pkl')

if __name__ == "__main__":

    engine = get_mysql_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    check_connection(engine)
    df_cmd, df_ville, df_tspt = get_datas_from_db(session)

    train_model(df_cmd)
