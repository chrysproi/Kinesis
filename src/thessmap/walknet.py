"""The pedestrian network, as a routable graph.

Not a display layer. Its whole purpose is to answer distance questions
along the ways people can actually walk, rather than as the crow flies —
which on this network overstates reach by about a factor of three.

Two analyses are built on it:

* `bus_metro_integration` — which bus stops, and how many distinct bus
  lines, are within a short walk of each Metro station.
* `walking_catchment` — the area actually reachable on foot from each
  station in 5 and 10 minutes.

Both are ordinary graph problems once the network is *noded*, which is
the step that matters. The sources are exported one file per highway
type, so a footway meeting a residential street shares an interior
vertex rather than an endpoint: 72% of raw endpoints have degree 1, and a
graph built straight from them barely connects. `unary_union` splits
every line at every crossing, after which 93% of nodes fall in a single
component.
"""

from dataclasses import dataclass

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.ops import unary_union

from . import config

# One file per highway type, per the brief's list. Ordered from the most
# to the least pedestrian: informative only, since all of them are
# walkable and the graph does not weight by comfort.
WALK_SOURCES = [
    "walk_pedestrian",
    "walk_footway",
    "walk_path",
    "walk_hiking",
    "walk_living_street",
    "walk_residential",
    "walk_tertiary",
    "walk_secondary",
    "walk_primary",
    "walk_trunk",
]

# Coordinates are rounded to this many decimals before becoming node
# keys. In EPSG:2100 that is centimetres — fine enough never to merge
# two real junctions, coarse enough that float noise cannot split one.
NODE_PRECISION = 2

# A stop or station further than this from any walkable way is not
# reachable on foot, and snapping it anyway would attach it to whatever
# happened to be nearest. Bus stops run to 751 m from the network —
# interurban poles on trunk roads — and silently routing those from the
# wrong street is worse than reporting them as unreachable.
MAX_SNAP_DISTANCE = 120

# Walking speed, for turning minutes into metres. 4.8 km/h is the usual
# planning figure for an average adult on level ground.
WALK_SPEED_M_PER_MIN = 80

# The two thresholds the brief asks for
CATCHMENT_MINUTES = (5, 10)

# How far a reachable edge spreads when catchment lines become a polygon.
# Half a street block: enough to read as an area rather than a spider,
# without claiming the backs of buildings are walkable.
CATCHMENT_BUFFER = 20

# Pulled back in after buffering, so the outline hugs the streets rather
# than bulging past the last reachable node.
CATCHMENT_EROSION = 8


@dataclass
class WalkNetwork:
    """A noded pedestrian graph plus the lookups routing needs."""

    graph: nx.Graph
    # The largest connected component, which is what anything gets
    # snapped to — see snap().
    component: set
    edges: dict           # frozenset({node, node}) -> LineString
    _nodes: np.ndarray
    _tree: cKDTree

    @property
    def connectivity(self):
        """Share of nodes reachable within the main component."""
        return len(self.component) / self.graph.number_of_nodes()

    def snap(self, points):
        """
        Nearest graph node per point, restricted to the main component.

        Restricted deliberately. Snapping to the nearest node full stop
        put three Metro stations onto isolated fragments, where routing
        reached three nodes instead of a neighbourhood. Staying on the
        main component costs at most a few metres of offset and is the
        difference between a result and a silent zero.

        Returns:
            (nodes, distances) with None and inf where the nearest
            candidate is beyond MAX_SNAP_DISTANCE.
        """

        coordinates = np.c_[points.geometry.x.values, points.geometry.y.values]
        distances, indices = self._tree.query(coordinates)

        nodes = [
            tuple(self._nodes[index]) if distance <= MAX_SNAP_DISTANCE else None
            for distance, index in zip(distances, indices)
        ]
        distances = np.where(distances <= MAX_SNAP_DISTANCE, distances, np.inf)

        return nodes, distances

    def reachable(self, node, metres):
        """{node: walking distance} within `metres` of a starting node."""
        return nx.single_source_dijkstra_path_length(
            self.graph, node, cutoff=metres, weight="weight"
        )


def _key(x, y):
    return (round(x, NODE_PRECISION), round(y, NODE_PRECISION))


def build(raw=None, sources=None, verbose=True):
    """
    Read every walkable source, node it, and return the graph.

    Takes a few seconds and holds ~60k nodes, so callers building both
    analyses should build once and pass it along.
    """

    raw = raw or config.RAW
    sources = sources or WALK_SOURCES

    parts = []
    for name in sources:
        path = raw / f"{name}.gpkg"
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing walkable layer: {path}\n"
                "Expected one GeoPackage per highway type; see WALK_SOURCES."
            )
        layer = gpd.read_file(path)[["geometry"]]
        if layer.crs is None:
            layer = layer.set_crs(epsg=config.SOURCE_CRS)
        parts.append(layer.to_crs(epsg=config.SOURCE_CRS))
        if verbose:
            print(f"  {name:<22} {len(layer):>6} segments")

    combined = gpd.GeoDataFrame(
        pd.concat(parts, ignore_index=True), crs=f"EPSG:{config.SOURCE_CRS}"
    )

    # The step the whole module depends on: split every line at every
    # crossing, so a footway meeting a street becomes a junction.
    noded = unary_union(combined.geometry.values)
    segments = list(getattr(noded, "geoms", [noded]))

    graph = nx.Graph()
    edges = {}

    for segment in segments:
        coordinates = segment.coords
        start = _key(*coordinates[0])
        end = _key(*coordinates[-1])
        if start == end:
            continue
        graph.add_edge(start, end, weight=segment.length)
        edges[frozenset((start, end))] = segment

    component = max(nx.connected_components(graph), key=len)
    nodes = np.array(list(component))

    network = WalkNetwork(
        graph=graph,
        component=component,
        edges=edges,
        _nodes=nodes,
        _tree=cKDTree(nodes),
    )

    if verbose:
        print(f"  noded {len(combined):,} -> {len(segments):,} segments")
        print(f"  graph {graph.number_of_nodes():,} nodes, "
              f"{graph.number_of_edges():,} edges")
        print(f"  main component holds {network.connectivity:.1%} of nodes")

    return network


# --------------------------------------------------
# Bus-Metro integration
# --------------------------------------------------


def _lines_of(value):
    """The distinct bus lines in a comma-separated LINES field."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return set()
    return {part.strip() for part in str(value).split(",") if part.strip()}


def bus_metro_integration(stations, stops, network=None, metres=300,
                          name_column=None, lines_column="lines_ejyp",
                          verbose=True):
    """
    Bus stops and distinct bus lines within a short walk of each station.

    Args:
        stations / stops: point GeoDataFrames, any CRS.
        network: a built WalkNetwork. Built here if omitted.
        metres: walking-distance threshold along the network.
        name_column: station name column; guessed if omitted.
        lines_column: the stops' comma-separated line list.

    Returns:
        A GeoDataFrame of stations with METRO_NAME, BUS_STOPS_NEAR,
        BUS_LINES_NEAR and BUS_LINES — the deduplicated line list, which
        is what makes the count auditable.
    """

    network = network or build(verbose=verbose)

    stations = _as_points(stations, network)
    stops = _as_points(stops, network)

    name_column = name_column or _name_column(stations)

    station_nodes, _ = network.snap(stations)
    stop_nodes, stop_distances = network.snap(stops)

    # Stops indexed by the node they snapped to, so a lookup is O(1) per
    # reachable node instead of a scan per station
    stops_at = {}
    for index, node in enumerate(stop_nodes):
        if node is not None:
            stops_at.setdefault(node, []).append(index)

    unreachable = int(np.isinf(stop_distances).sum())
    if verbose and unreachable:
        print(f"  {unreachable} of {len(stops)} stops are further than "
              f"{MAX_SNAP_DISTANCE} m from any walkable way, so excluded")

    rows = []

    for position, node in enumerate(station_nodes):
        station = stations.iloc[position]
        found = []

        if node is not None:
            for reached in network.reachable(node, metres):
                found.extend(stops_at.get(reached, []))

        lines = set()
        for index in found:
            lines |= _lines_of(stops.iloc[index].get(lines_column))

        rows.append({
            "METRO_NAME": station.get(name_column),
            "BUS_STOPS_NEAR": len(found),
            "BUS_LINES_NEAR": len(lines),
            # Sorted so the column is stable between runs
            "BUS_LINES": ",".join(sorted(lines)),
            "walk_threshold_m": metres,
            "geometry": station.geometry,
        })

    return gpd.GeoDataFrame(rows, geometry="geometry", crs=stations.crs)


# --------------------------------------------------
# Walking catchment
# --------------------------------------------------


def walking_catchment(stations, network=None, minutes=CATCHMENT_MINUTES,
                      name_column=None, verbose=True):
    """
    The area actually reachable on foot from each station.

    One row per station per threshold, so the result is tidy and drops
    straight into a GeoPackage or a GeoJSON layer.

    Built by buffering the reachable *edges* rather than hulling the
    reachable nodes: a convex hull would claim everything between two
    streets, including the blocks in between, which is exactly the
    overstatement using the network was meant to avoid.
    """

    network = network or build(verbose=verbose)

    stations = _as_points(stations, network)
    name_column = name_column or _name_column(stations)

    nodes, _ = network.snap(stations)
    core = network.graph.subgraph(network.component)

    rows = []

    for position, node in enumerate(nodes):
        station = stations.iloc[position]

        for span in minutes:
            metres = span * WALK_SPEED_M_PER_MIN
            polygon = None

            if node is not None:
                reached = network.reachable(node, metres)
                segments = [
                    network.edges[frozenset(edge)]
                    for edge in core.subgraph(reached).edges()
                    if frozenset(edge) in network.edges
                ]
                if segments:
                    polygon = (unary_union(segments)
                               .buffer(CATCHMENT_BUFFER, resolution=4)
                               .buffer(-CATCHMENT_EROSION))

            rows.append({
                "METRO_STATION": station.get(name_column),
                "minutes": span,
                "metres": metres,
                "area_km2": round(polygon.area / 1e6, 4) if polygon else 0.0,
                "geometry": polygon,
            })

    catchments = gpd.GeoDataFrame(rows, geometry="geometry", crs=stations.crs)

    if verbose:
        for span in minutes:
            band = catchments[catchments.minutes == span]
            circle = np.pi * (span * WALK_SPEED_M_PER_MIN) ** 2 / 1e6
            print(f"  {span} min: median {band.area_km2.median():.2f} km2, "
                  f"{band.area_km2.median() / circle:.0%} of a "
                  f"{span * WALK_SPEED_M_PER_MIN:.0f} m circle")

    return catchments


# --------------------------------------------------
# Shared helpers
# --------------------------------------------------


def _as_points(gdf, network):
    """Points in the network's CRS, multipart geometry exploded."""

    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=config.SOURCE_CRS)

    gdf = gdf.to_crs(f"EPSG:{config.SOURCE_CRS}")
    gdf = gdf.explode(index_parts=False)

    return gdf[gdf.geom_type == "Point"].reset_index(drop=True)


def _name_column(gdf):
    """Whichever name column this layer happens to carry."""

    for candidate in ("name", "name:el", "name_el", "station", "NAME",
                      "onomastasi"):
        if candidate in gdf.columns:
            return candidate

    raise KeyError(
        f"No name column found. Tried name / name:el / station; "
        f"layer has {', '.join(gdf.columns)}"
    )
