"""Classifying a continuous indicator into map classes.

Kept apart from `webexport` because the choice of scheme is a
cartographic decision, not a rendering detail, and because the breaks
have to be identical in the fill expression and in the legend.
"""

import mapclassify

# Natural Breaks (Jenks), matching what QGIS produces for the same
# column. Switch to "quantiles" to spread the classes evenly by count:
# population density here is bimodal — six dense municipalities from
# 4,000 to 14,936/km2, then a hard gap down to eight from 25 to 462 —
# so Jenks is mathematically right but spends three of its five classes
# on one municipality each and puts 8 of 14 in the lightest shade.
SCHEMES = {
    "jenks": mapclassify.NaturalBreaks,
    "quantiles": mapclassify.Quantiles,
    "equal": mapclassify.EqualInterval,
}

DEFAULT_SCHEME = "jenks"


def breaks(values, classes=5, scheme=DEFAULT_SCHEME):
    """
    Upper bounds of each class, longest-first as MapLibre `step` wants.

    Args:
        values: the column to classify.
        classes: how many classes.
        scheme: a key of SCHEMES.

    Returns:
        A list of `classes` upper bounds, ascending. The last equals the
        maximum, so it never appears as a step stop — `step` needs the
        classes - 1 interior breaks, and the legend needs all of them.
    """

    if scheme not in SCHEMES:
        raise ValueError(
            f"Unknown scheme {scheme!r}. Known: {', '.join(sorted(SCHEMES))}"
        )

    classifier = SCHEMES[scheme](values, k=classes)

    return [float(bound) for bound in classifier.bins]


def legend_ranges(values, classes=5, scheme=DEFAULT_SCHEME):
    """
    (lower, upper) per class, for legend labels.

    The lower bound of the first class is the data minimum rather than
    zero: no municipality here is uninhabited, and a legend reading
    "0 - 462" would imply one is.
    """

    bounds = breaks(values, classes, scheme)
    lowers = [float(min(values))] + bounds[:-1]

    return list(zip(lowers, bounds))
