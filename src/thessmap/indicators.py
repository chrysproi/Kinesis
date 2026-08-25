"""The socio-demographic indicators of section 2."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Indicator:
    """One mappable column of the municipalities layer."""

    id: str
    column: str
    label: str
    unit: str
    decimals: int = 0
    short: str | None = None
    mapped: bool = False

    @property
    def layer_id(self):
        return f"ind_{self.id}"


INDICATORS = [
    Indicator("pop_density", "POP_DENS",
              "Population density \u2014 Municipality level",
              "inhab./km\u00b2",
              short="By municipality",
              mapped=True),

    Indicator("population", "POP_2021",
              "Population 2021", "inhabitants"),

    Indicator("age60", "AGE60_PCT",
              "Population aged 60+", "% of population", decimals=1),

    Indicator("unemployment", "UNEMP_PCT",
              "Unemployment", "% of labour force", decimals=1),

    Indicator("higher_education", "HIGHEDU_PCT",
              "Higher education", "% of population", decimals=1),

    Indicator("no_car", "NOCAR_PCT",
              "Households without a car", "% of households", decimals=1),
]

MAPPED = [indicator for indicator in INDICATORS if indicator.mapped]
BY_ID = {indicator.id: indicator for indicator in INDICATORS}
BY_LAYER = {indicator.layer_id: indicator for indicator in INDICATORS}
