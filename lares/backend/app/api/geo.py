from geoalchemy2.shape import to_shape


def geom_centroid_lonlat(geom) -> tuple[float, float] | None:
    if geom is None:
        return None
    shape = to_shape(geom)
    c = shape.centroid
    return (c.x, c.y)
