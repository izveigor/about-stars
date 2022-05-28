from functools import partial
from multiprocessing import Manager, Pool, cpu_count
from typing import Any, Union

import click
import numpy as np
import pandas as pd
from flask import Blueprint
from sqlalchemy import text

from models import Catalog, CatalogAssociation, Constellation, Star, db

from .constants import (
    CATALOGS,
    CONSTELLATION,
    DEC,
    INT_CATALOGS,
    LIST_OF_CONSTELLATIONS,
    OTHER_DATA,
    PATH_TO_HYGDATA_V3,
    RA,
    SPECT,
    STELLAR_CLASSIFICATION,
    STR_CATALOGS,
)

bp_cli = Blueprint("api", __name__)


def create_views_for_constellation(constellations: list[Constellation]) -> None:
    for constellation in constellations:
        constellation_view = text(
            f"""
            CREATE VIEW stars_with_{constellation.tag} AS
                SELECT * FROM star WHERE con='{constellation.tag}';
        """
        )
        db.session.execute(constellation_view)
        db.session.commit()


def get_spect(spect_from_line: str) -> Union[str, None]:
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


def add_star(
    stars: list[Star],
    catalog_associations: list[CatalogAssociation],
    line: dict[str, Any],
) -> None:
    constellation = line[CONSTELLATION]

    star = Star(
        id=int(line["id"]),
        **{key: line[key] for key in OTHER_DATA},
        spect=get_spect(line[SPECT]),
        ra=line[RA],
        dec=line[DEC],
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


def create_catalogs() -> None:
    click.echo(f"\nStart downloading catalogs")
    for tag in CATALOGS:
        catalog_model_instance = Catalog(tag=tag)
        click.echo(f'Added catalog with tag: "{tag}"')
        db.session.add(catalog_model_instance)

    db.session.commit()
    click.echo("All catalogs have successfully saved in the database")


def create_constellations() -> None:
    click.echo(f"\nStart downloading constellations ({len(LIST_OF_CONSTELLATIONS)})")
    constellations = [Constellation(tag=tag) for tag in LIST_OF_CONSTELLATIONS]
    db.session.bulk_save_objects(constellations)
    click.echo("Saving constellations in the database...")
    db.session.commit()
    click.echo("Creating views for constellations")
    create_views_for_constellation(constellations)
    click.echo("Constellations have successfully saved in the database")


def get_api() -> None:
    hygdata = pd.read_csv(PATH_TO_HYGDATA_V3)
    data = hygdata.replace(np.nan, None)
    create_constellations()
    create_catalogs()

    click.echo(f"\nStart downloading stars ({len(data)})")

    with click.progressbar(
        range(len(data)), label="Download stars:"
    ) as stars_bar, Manager() as manager:
        stars: list[Star] = manager.list()
        catalog_associations: list[CatalogAssociation] = manager.list()

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


@bp_cli.cli.command("download_stars")  # type: ignore
def download_stars() -> None:
    click.echo(
        f'Start downloading information about stars from file "{PATH_TO_HYGDATA_V3}"'
    )
    get_api()
    click.echo("Information about stars have successfully downloaded!")
