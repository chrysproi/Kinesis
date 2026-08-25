"""The pedestrian network, as a routable graph."""

from dataclasses import dataclass

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.ops import unary_union

from . import config

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

NODE_PRECISION = 2
MAX_SNAP_DISTANCE = 120
WALK_SPEED_M_PER_MIN = 80
CATCHMENT_MINUTES = (5, 10)
CATCHMENT_BUFFER = 20
CATCHMENT_EROSION = 8


@dataclass
class WalkNetwork:
    """A noded pedestrian graph plus the lookups routing needs."""

    graph: nx.Graph
    component: set
    edges: dict
    _nodes: np.ndarray
    _tree: cKDTree

    @property
    def connectivity(self):
        """Share of nodes reachable within the main component."""
        return len(self.component) / self.graph.number_of_nodes()

    def snap(self, points):
        """Nearest graph node per point, restricted to the main component."""

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
    """Read every walkable source, node it, and return the graph."""

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


def _lines_of(value):
    """The distinct bus lines in a comma-separated LINES field."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return set()
    return {part.strip() for part in str(value).split(",") if part.strip()}


def bus_metro_integration(stations, stops, network=None, metres=300,
                          name_column=None, lines_column="lines_ejyp",
                          verbose=True):
    """Bus stops and distinct bus lines within a short walk of each station."""

    network = network or build(verbose=verbose)

    stations = _as_points(stations, network)
    stops = _as_points(stops, network)

    name_column = name_column or _name_column(stations)

    station_nodes, _ = network.snap(stations)
    stop_nodes, stop_distances = network.snap(stops)

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
            "BUS_LINES": ",".join(sorted(lines)),
            "walk_threshold_m": metres,
            "geometry": station.geometry,
        })

    return gpd.GeoDataFrame(rows, geometry="geometry", crs=stations.crs)


def walking_catchment(stations, network=None, minutes=CATCHMENT_MINUTES,
                      name_column=None, verbose=True):
    """The area actually reachable on foot from each station."""

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
