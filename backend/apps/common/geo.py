"""Bridge between stryde_core (lat, lon tuples) and GeoDjango (GEOS uses x=lon, y=lat)."""

from django.contrib.gis.geos import LineString, MultiPoint, Point

LatLon = tuple[float, float]


def point(p: LatLon) -> Point:
    return Point(p[1], p[0], srid=4326)


def line(pts: list[LatLon]) -> LineString:
    return LineString([(lon, lat) for lat, lon in pts], srid=4326)


def multipoint(pts: list[LatLon]) -> MultiPoint:
    return MultiPoint([point(p) for p in pts], srid=4326)


def latlon(p: Point) -> LatLon:
    return (p.y, p.x)


def latlons(geom) -> list[LatLon]:
    return [(y, x) for x, y, *_ in geom.coords] if hasattr(geom, "coords") else []
