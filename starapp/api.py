import pandas as pd
from .constants import (
    CATALOGS,
    INT_CATALOGS,
    STR_CATALOGS,
    POINT,
    SPECT,
    OTHER_DATA,
    CONSTELLATION,
    STELLAR_CLASSIFICATION,
    PATH_TO_HYGDATA_V3,
    LIST_OF_CONSTELLATIONS,
)
from models import Catalog, CatalogAssociation, Constellation, Star, db
import numpy as np
import click
from flask import Blueprint
from multiprocessing import Pool, Manager, cpu_count
from functools import partial
from sqlalchemy import text


bp_cli = Blueprint("api", __name__)


def create_views_for_constellation(constellations):
    for constellation in constellations:
        constellation_view = text(
            f"""
            CREATE VIEW stars_with_{constellation.tag} AS
                SELECT * FROM star WHERE con='{constellation.tag}';
        """
        )
        db.session.execute(constellation_view)
        db.session.commit()


def get_spect(spect_from_line):
    spect = None
    try:
        classification = spect_from_line[0]
        if classification in STELLAR_CLASSIFICATION:
            spect = classification
        else:
            spect = None
    except:
        spect = None

    return spect


def add_star(stars, catalog_associations, line):
    constellation = line[CONSTELLATION]

    star = Star(
        id=int(line["id"]),
        **{key: line[key] for key in OTHER_DATA},
        spect=get_spect(line[SPECT]),
        ra=line[POINT[0]],
        dec=line[POINT[1]],
        con=constellation.lower() if constellation is not None else None,
    )

    stars.append(star)

    for catalog_type, func in zip((INT_CATALOGS, STR_CATALOGS), (int, str)):
        for catalog in catalog_type:
            if line[catalog] is not None:
                catalog_association = CatalogAssociation(
                    star_id=star.id, catalog_tag=catalog, identifier=func(line[catalog])
                )
                catalog_associations.append(catalog_association)


def create_catalogs():
    click.echo(f"\nStart downloading catalogs")
    for tag in CATALOGS:
        catalog_model_instance = Catalog(tag=tag)
        click.echo(f'Added catalog with tag: "{tag}"')
        db.session.add(catalog_model_instance)

    db.session.commit()
    click.echo("All catalogs have successfully saved in the database")


def create_constellations():
    click.echo(f"\nStart downloading constellations ({len(LIST_OF_CONSTELLATIONS)})")
    constellations = [Constellation(tag=tag) for tag in LIST_OF_CONSTELLATIONS]
    db.session.bulk_save_objects(constellations)
    click.echo("Saving constellations in the database...")
    db.session.commit()
    click.echo("Creating views for constellations")
    create_views_for_constellation(constellations)
    click.echo("Constellations have successfully saved in the database")


def get_api():
    hygdata = pd.read_csv(PATH_TO_HYGDATA_V3)
    data = hygdata.replace(np.nan, None)
    create_constellations()
    create_catalogs()

    click.echo(f"\nStart downloading stars ({len(data)})")

    with click.progressbar(
        range(len(data)), label="Download stars:"
    ) as stars_bar, Manager() as manager:
        stars = manager.list()
        catalog_associations = manager.list()

        with Pool(cpu_count() - 1) as pool:
            pool.map(
                partial(add_star, stars, catalog_associations),
                [data.loc[index] for index in stars_bar],
            )

        click.echo("\nSaving stars in the database...")

        db.session.bulk_save_objects(stars)
        db.session.bulk_save_objects(catalog_associations)

        db.session.commit()

        click.echo("Stars have successfully saved in the database")


@bp_cli.cli.command("download_stars")
def download_stars():
    click.echo(
        f'Start downloading information about stars from file "{PATH_TO_HYGDATA_V3}"'
    )
    get_api()
    click.echo("Information about stars have successfully downloaded!")
