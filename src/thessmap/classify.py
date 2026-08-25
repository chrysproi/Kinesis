"""Classifying a continuous indicator into map classes."""

import mapclassify

SCHEMES = {
    "jenks": mapclassify.NaturalBreaks,
    "quantiles": mapclassify.Quantiles,
    "equal": mapclassify.EqualInterval,
}

DEFAULT_SCHEME = "jenks"


def breaks(values, classes=5, scheme=DEFAULT_SCHEME):
    """Upper bounds of each class, longest-first as MapLibre `step` wants."""

    if scheme not in SCHEMES:
        raise ValueError(
            f"Unknown scheme {scheme!r}. Known: {', '.join(sorted(SCHEMES))}"
        )

    classifier = SCHEMES[scheme](values, k=classes)

    return [float(bound) for bound in classifier.bins]


def legend_ranges(values, classes=5, scheme=DEFAULT_SCHEME):
    """(lower, upper) per class, for legend labels."""

    bounds = breaks(values, classes, scheme)
    lowers = [float(min(values))] + bounds[:-1]

    return list(zip(lowers, bounds))
