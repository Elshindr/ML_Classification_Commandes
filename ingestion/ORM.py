from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()


class Ville(Base):
    __tablename__ = "ville"
    idVille = Column(Integer, primary_key=True, unique=True)
    name = Column(String(25), nullable=False)


class Client(Base):
    __tablename__ = "client"
    idClient = Column(String(25), primary_key=True, unique=True)
    idVille = Column(Integer, ForeignKey(Ville.idVille), nullable=False)
    rel_ville_cli = relationship("Ville")


class Transporteur(Base):
    __tablename__ = "transporteur"
    idTransporteur = Column(Integer, primary_key=True, unique=True)
    name = Column(String(25), nullable=False)


class Commande(Base):
    __tablename__ = "commande"
    idCommande= Column(String(25), primary_key=True, unique=True)
    idClient = Column(String(25), ForeignKey(Client.idClient), nullable=False)
    idTransporteur = Column(Integer, ForeignKey(Transporteur.idTransporteur), nullable=False)
    dateCommande = Column(DateTime, nullable=False)
    datePrevue = Column(DateTime, nullable=False)
    dateReelle = Column(DateTime, nullable=False)
    poidsKg = Column(Float, nullable=False)
    distanceKm = Column(Float, nullable=False)
    nbArticle = Column(Integer, nullable=False)
    statut=Column(String(10), nullable=False)
    jourRetard = Column(Integer, nullable=False)
    niveauRetard=Column(String(25), nullable=False)
    rel_idClient_commande = relationship("Client")
    rel_idTransporteur_commande = relationship("Transporteur")
