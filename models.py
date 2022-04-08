from flask_sqlalchemy import SQLAlchemy
from starapp.constants import STELLAR_CLASSIFICATION

db = SQLAlchemy()


class Constellation(db.Model):
    __tablename__ = 'constellation'
    tag = db.Column(db.String(3), primary_key=True)
    stars = db.relationship('Star', backref='star', lazy=True)


class Star(db.Model):
    __tablename__ = 'star'
    id = db.Column(db.Integer, primary_key=True)
    dist = db.Column(db.Float, nullable=False)
    mag = db.Column(db.Float, nullable=False)
    absmag = db.Column(db.Float, nullable=False)
    spect = db.Column(db.Enum(*STELLAR_CLASSIFICATION, name='spect'), nullable=True)
    con = db.Column(db.String(3), db.ForeignKey('constellation.tag'), nullable=True)
    ra = db.Column(db.Float, nullable=False)
    dec = db.Column(db.Float, nullable=False)


class Catalog(db.Model):
    __tablename__ = 'catalog'
    tag = db.Column(db.String(10), primary_key=True)
    catalog_associations = db.relationship('CatalogAssociation')


class CatalogAssociation(db.Model):
    __tablename__ = 'catalog_association'
    catalog_tag = db.Column(db.String(10), db.ForeignKey('catalog.tag'), primary_key=True)
    star_id = db.Column(db.Integer, db.ForeignKey('star.id'), primary_key=True)
    identifier = db.Column(db.String(30))
    star = db.relationship('Star')
