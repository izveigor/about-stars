from flask import render_template, Blueprint, jsonify, request, session
from .geometry import is_points_range_valid, is_polygon_contains_point, Graham_scan
from models import db, Constellation, CatalogAssociation, Star
from sqlalchemy import text
from collections import Counter
from .constants import (
    ERROR_IS_POINTS_RANGE_VALID,
    ERROR_NOT_ENOUGH_POINTS,
    ERROR_CONSTELLATION_DOES_NOT_EXIST,
    POINT,
    SPECT,
    CONSTELLATION,
    OTHER_DATA,
    CATALOGS,
    REDIS_SETTINGS,
)
from .algorithms import Search, TypeSearch
import string
import random


bp_views = Blueprint("views", __name__)


def get_hash():
    alphabet = string.hexdigits[:-6]
    random_hash = ""
    for i in range(64):
        random_hash += alphabet[random.randint(0, len(alphabet) - 1)]

    return random_hash


@bp_views.route("/", methods=["GET"])
def main():
    return render_template("index.html")


@bp_views.route("/about", methods=["GET"])
def about():
    return render_template("about.html")


@bp_views.route("/delete_all", methods=["GET"])
def delete_all():
    hash_ = session.get("request")
    if hash_ is not None:
        Search.clear(hash_=hash_)
        session.pop("request")

    return jsonify()


def _result_from_stars_with_constellation_to_dict(tag):
    star_fields = POINT + (SPECT, "id", CONSTELLATION) + OTHER_DATA
    star_fields_str = ""
    for star_field in star_fields:
        star_fields_str += star_field + ","

    star_fields_str = star_fields_str[:-1]
    stars = [
        {key: field for key, field in zip(star_fields, row)}
        for row in db.session.execute(
            text(
                f"""
                    SELECT {star_fields_str} FROM stars_with_{tag};
                """
            )
        ).fetchall()
    ]
    return stars, len(stars)


@bp_views.route("/search_constellation", methods=["POST"])
def get_data_from_constellation():
    tag = request.json["tag"]
    if Constellation.query.get(tag) is not None:
        create_stars_with_constellation = text(
            f"""
                CREATE VIEW stars_with_catalogs AS
                    SELECT * FROM catalog_association RIGHT OUTER JOIN stars_with_{tag}
                    ON catalog_association.star_id=stars_with_{tag}.id;
            """
        )

        catalog_search = text(
            """
                SELECT catalog_tag, (CAST(count(*) AS float) / CAST((SELECT count(*) 
                FROM stars_with_catalogs) AS float) * 100)
                FROM stars_with_catalogs GROUP BY catalog_tag;
            """
        )

        spect_search = text(
            f"""
                SELECT spect, (CAST(count(*) AS float) / CAST((SELECT count(*) 
                FROM stars_with_{tag}) AS float) * 100)
                FROM stars_with_{tag} GROUP BY spect;
            """
        )

        db.session.execute(create_stars_with_constellation)

        catalogs = [
            {key: field for key, field in zip(("tag", "percentage"), catalog)}
            for catalog in db.session.execute(catalog_search)
        ]
        spects = [
            {key: field for key, field in zip(("spect", "percentage"), spect)}
            for spect in db.session.execute(spect_search)
        ]

        session_request = session.get("request")
        if session_request is not None:
            old_hash = session_request
            session.pop("request")
            Search.clear(hash_=old_hash)

        hash_ = get_hash()
        session["request"] = hash_

        stars, number_of_stars = _result_from_stars_with_constellation_to_dict(tag)
        for type_search in TypeSearch:
            Search(hash_, type_search, stars=stars)

        return jsonify(
            {
                "number_of_stars": number_of_stars,
                "catalogs": sorted(
                    catalogs, key=lambda x: x["percentage"], reverse=True
                ),
                "spects": sorted(spects, key=lambda x: x["percentage"], reverse=True),
                "constellations": [{"tag": tag, "percentage": 100}],
            }
        )
    else:
        return jsonify(
            {
                "error": ERROR_CONSTELLATION_DOES_NOT_EXIST,
            }
        )


def _counter_with_percentage(counter, field):
    with_percentage = list()
    length_counter = 0
    for value in counter.values():
        length_counter += value

    for key in counter.keys():
        with_percentage.append(
            {
                field: key,
                "percentage": counter[key] / length_counter * 100,
            }
        )
    return sorted(with_percentage, key=lambda x: x["percentage"], reverse=True)


@bp_views.route("/search_points", methods=["POST"])
def get_data_with_points():
    points = request.json
    if isinstance(points, list):
        for point in points:
            if not isinstance(point, dict):
                return "bad request", 400

            if list(point.keys()) != ["ra", "dec"]:
                return "bad request", 400
    else:
        return "bad request", 400

    if len(points) < 3:
        return jsonify({"error": ERROR_NOT_ENOUGH_POINTS})

    if is_points_range_valid(points):
        stars = []
        convex_polygon = Graham_scan(points)
        spects, catalogs, constellations = (Counter() for i in range(3))
        for star in Star.query.all():
            if is_polygon_contains_point(points, star.ra, star.dec):
                star_dict = vars(star)
                star_dict.pop("_sa_instance_state")
                stars.append(star_dict)
                spects.update([star.spect])
                catalogs.update(
                    [
                        catalog_association.catalog_tag
                        for catalog_association in CatalogAssociation.query.filter_by(
                            star_id=star.id
                        )
                    ]
                )
                constellations.update([star.con])

        session_request = session.get("request")
        if session_request is not None:
            old_hash = session_request
            session.pop("request")
            Search.clear(hash_=old_hash)

        hash_ = get_hash()
        session["request"] = hash_

        for type_search in TypeSearch:
            Search(hash_, type_search, stars=stars)

        return jsonify(
            {
                "number_of_stars": len(stars),
                "catalogs": _counter_with_percentage(catalogs, "tag"),
                "spects": _counter_with_percentage(spects, "spect"),
                "constellations": _counter_with_percentage(constellations, "tag"),
            }
        )
    else:
        return jsonify({"error": ERROR_IS_POINTS_RANGE_VALID})


@bp_views.route("/segment_search", methods=["POST"])
def segment_search():
    type_ = request.json["type"]
    minimum = float(request.json["minimum"])
    maximum = float(request.json["maximum"])

    try:
        type_enum = TypeSearch(type_)
    except:
        return "bad request", 400

    hash_ = session.get("request")
    if hash_ is None:
        return "bad request", 400

    search_class = Search(hash_, type_enum)

    result = search_class.segment_search(minimum, maximum)

    return jsonify(result)


@bp_views.route("/sort_search", methods=["POST"])
def sort_search():
    type_ = request.json["type"]
    page = request.json["page"]
    descending = request.json["descending"]

    try:
        type_enum = TypeSearch(type_)
    except:
        return "bad request", 400

    hash_ = session.get("request")
    if hash_ is None:
        return "bad request", 400

    search_class = Search(hash_, type_enum)

    result = search_class.sort_search(page=page, descending=bool(int(descending)))

    return jsonify(result)
