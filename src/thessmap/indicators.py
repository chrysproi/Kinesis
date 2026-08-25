"""The socio-demographic indicators of section 2.

Every indicator is exported — the columns ride along on the
municipalities layer whatever happens here — but only those marked
`mapped` get a choropleth, a legend card and a sidebar switch.

The rest are inputs to the hub siting, not map layers. Seven mutually
exclusive area fills over the same fourteen polygons made a switch list
where six of the options had to be off, and none of them answers a
question you look at the map to ask: "which municipality has the highest
unemployment" is a table, while "where is the population" is a map.
They stay in the data for scoring candidate hub locations.

The question these answer, per the brief: which areas have the greatest
potential need for alternative mobility and better access to shared
transport. That is why NOCAR_PCT is here and, for instance, household
income is not — the list is the demand side of a mobility argument.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Indicator:
    """One mappable column of the municipalities layer."""

    id: str                 # registry layer id
    column: str             # column in the municipalities layer
    label: str              # full name: popup eyebrow, tooltip, legend
    unit: str               # legend caption
    decimals: int = 0       # how many to show in legend break labels
    # Shown in the sidebar row when the full name would truncate. The
    # section header already says POPULATION, so the row does not have to.
    short: str | None = None
    # Whether the map draws it. False means the column is still exported
    # and still in the popup, but there is no layer, legend or switch.
    mapped: bool = False

    @property
    def layer_id(self):
        return f"ind_{self.id}"


INDICATORS = [
    # Population density leads: it is the one indicator that is also a
    # measure of how many people any of the others applies to.
    # Named per the brief. "Municipality level" is the whole point of the
    # name — it is what separates this from the 100 m grid, which is the
    # same measure at a different resolution.
    Indicator("pop_density", "POP_DENS",
              "Population density \u2014 Municipality level",
              # Unit only, no provenance. The 100 m grid shares this
              # legend card — same classes, same ramp — but comes from
              # GHSL 2020 rather than ELSTAT 2021, so a source stamped on
              # the shared card would be wrong half the time. Each
              # layer's own label carries its source instead.
              "inhab./km\u00b2",
              short="By municipality",
              mapped=True),

    Indicator("population", "POP_2021",
              "Population 2021", "inhabitants"),

    # The three ELSTAT percentages that bear on mobility need
    Indicator("age60", "AGE60_PCT",
              "Population aged 60+", "% of population", decimals=1),

    Indicator("unemployment", "UNEMP_PCT",
              "Unemployment", "% of labour force", decimals=1),

    Indicator("higher_education", "HIGHEDU_PCT",
              "Higher education", "% of population", decimals=1),

    # The most direct measure of latent demand for alternatives to the
    # private car, and the reason this section exists
    Indicator("no_car", "NOCAR_PCT",
              "Households without a car", "% of households", decimals=1),
]

# Only these become layers; the rest are carried for the hub analysis
MAPPED = [indicator for indicator in INDICATORS if indicator.mapped]

BY_ID = {indicator.id: indicator for indicator in INDICATORS}
BY_LAYER = {indicator.layer_id: indicator for indicator in INDICATORS}
