"""Loading the layers the map draws from."""

from functools import cached_property

import geopandas as gpd

from . import config


class MapData:
    """Lazy, cached access to source and web-ready layers."""

    def __init__(self, raw=None, processed=None, bbox=None, simplify=None):
        """."""

        self.raw_dir = raw or config.RAW
        self.processed_dir = processed or config.PROCESSED
        self.bbox = bbox
        self.simplify = simplify


    def _trim(self, gdf):
        """Apply the bbox and simplification, if any."""

        if self.bbox is not None:
            min_lon, min_lat, max_lon, max_lat = self.bbox
            gdf = gdf.cx[min_lon:max_lon, min_lat:max_lat]

        if self.simplify:
            gdf = gdf.copy()
            gdf["geometry"] = gdf.geometry.simplify(
                self.simplify, preserve_topology=True
            )

        return gdf

    def raw(self, name):
        """Read a source GeoPackage, still in EPSG:2100."""
        path = self.raw_dir / f"{name}.gpkg"
        if not path.is_file():
            raise FileNotFoundError(f"Missing source layer: {path}")
        return gpd.read_file(path)

    def processed(self, name):
        """Read a web-ready layer, already clipped and in EPSG:4326."""
        path = self.processed_dir / f"{name}_web_4326.gpkg"
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing processed layer: {path}\n"
                "Run scripts/prepare_layers.py to build it."
            )
        return self._trim(gpd.read_file(path))


    @cached_property
    def units(self):
        """Administrative units carrying the `zone` column."""
        return self.raw("thess_units")

    @cached_property
    def units_4326(self):
        return self.units.to_crs(epsg=config.WEB_CRS)

    @cached_property
    def study_boundary(self):
        """All zones dissolved into one polygon. The spine of the project."""
        return self.units.dissolve()


    @cached_property
    def selected_lakes(self):
        """The three named lakes, deduplicated."""
        lakes = self.raw("selected_lakes").to_crs(epsg=config.WEB_CRS)

        before = len(lakes)
        lakes = lakes.drop_duplicates(subset="geometry").reset_index(drop=True)

        if len(lakes) != before:
            print(f"  selected_lakes: dropped {before - len(lakes)} "
                  "duplicate geometries")

        return self._trim(lakes)

    @cached_property
    def water_polygons(self):
        """Lakes, reservoirs, riverbanks and wetland, clipped and prepared."""
        return self.processed("water_polygons")

    @cached_property
    def water_points(self):
        """Weirs, dams, waterfalls and lock gates."""
        return self.processed("water_points")

    @cached_property
    def water_lines(self):
        """Rivers, streams, canals and drains, carrying `waterway`."""
        return self.processed("water_lines")


    @cached_property
    def buildings(self):
        return self.processed("buildings")

    @cached_property
    def buildings_height(self):
        """Surveyed footprints carrying ROOF_H, MAX_FLOOR and NO_APPART."""
        return self.processed("buildings_height")

    @cached_property
    def landuse(self):
        """14,456 parcels carrying LU_GROUP and the detailed landuse tag."""
        return self.processed("landuse")

    @cached_property
    def walkways(self):
        """The walkable network: pedestrian ways plus the road classes."""
        return self.processed("walkways")

    @cached_property
    def bus_lanes(self):
        return self.processed("bus_lanes")

    @cached_property
    def bike_lanes_primary(self):
        return self.processed("bike_lanes_primary")

    @cached_property
    def bike_lanes_secondary(self):
        return self.processed("bike_lanes_secondary")

    @cached_property
    def bike_lanes_proposed(self):
        return self.processed("bike_lanes_proposed")

    @cached_property
    def bike_parking(self):
        return self.processed("bike_parking")

    @cached_property
    def bike_rental(self):
        return self.processed("bike_rental")

    @cached_property
    def bike_points(self):
        """Parking stands and rental stations as one layer, tagged by kind."""
        import pandas as pd

        parts = []
        for kind, layer in (("parking", self.bike_parking),
                            ("rental", self.bike_rental)):
            part = layer[["geometry"]].copy()
            part["kind"] = kind
            parts.append(part)

        combined = pd.concat(parts, ignore_index=True)
        return gpd.GeoDataFrame(combined, geometry="geometry",
                                crs=self.bike_parking.crs)

    @cached_property
    def bus_stops(self):
        return self.processed("bus_stops")

    @cached_property
    def metro_line(self):
        return self.processed("metro_line")

    @cached_property
    def metro_stations(self):
        return self.processed("metro_stations")

    @cached_property
    def ferry_routes(self):
        return self.processed("ferry_routes")

    @cached_property
    def ferry_terminals(self):
        return self.processed("ferry_terminals")

    @cached_property
    def parking_places(self):
        return self.processed("parking_places")

    @cached_property
    def municipalities(self):
        """The 14 municipalities carrying the ELSTAT 2021 indicators."""
        return self.processed("municipalities")

    @cached_property
    def parking_points(self):
        """One point per parking place, for the dot and the P symbol."""
        return self.processed("parking_points")

    @cached_property
    def taxi_spots(self):
        return self.processed("taxi_spots")

    @cached_property
    def trees(self):
        return self.processed("trees")

    @cached_property
    def education_polygons(self):
        return self.processed("education_polygons")

    @cached_property
    def education_symbols(self):
        return self.processed("education_symbols")

    @cached_property
    def culture_polygons(self):
        return self.processed("culture_polygons")

    @cached_property
    def culture_lines(self):
        return self.processed("culture_lines")

    @cached_property
    def culture_symbols(self):
        return self.processed("culture_symbols")

    @cached_property
    def health_symbols(self):
        return self.processed("health_symbols")

    @cached_property
    def sport_symbols(self):
        return self.processed("sport_symbols")

    @cached_property
    def public_services_symbols(self):
        return self.processed("public_services_symbols")

    @cached_property
    def commercial_symbols(self):
        return self.processed("commercial_symbols")

    @cached_property
    def playground_symbols(self):
        """Playground points: standalone nodes plus one per mapped area."""
        return self.processed("playground_symbols")

    @cached_property
    def green_spaces(self):
        """Parks, green space, recreational space, forest and playgrounds."""
        return self.processed("green_spaces")

    @cached_property
    def squares(self):
        return self.processed("squares")

    @cached_property
    def hub_network(self):
        """222 scored candidate hub sites, in three tiers."""
        return self.processed("hub_network")


    def zone_outline(self, zone_name):
        """One dissolved outline for a single zone."""
        return self.units_4326[self.units_4326["zone"] == zone_name].dissolve()
