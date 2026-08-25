import { Marker, type GeoJSONSource, type Map as MapLibreMap } from "maplibre-gl";

import { CLUSTERED_SOURCES } from "../generated/layers";

/** Cluster badges as DOM markers: a raster basemap serves no glyphs. */
export function attachClusters(
  instance: MapLibreMap,
  sourceId: string,
  options: { color: string; isVisible: () => boolean },
) {
  const config = CLUSTERED_SOURCES[sourceId];
  if (!config) return;

  const markers = new Map<number, Marker>();

  const clear = () => {
    for (const marker of markers.values()) marker.remove();
    markers.clear();
  };

  const badge = (count: string) => {
    const element = document.createElement("button");
    element.type = "button";
    element.className = "tm-cluster";
    element.style.background = options.color;
    element.textContent = count;
    element.title = `${count} bike parking and rental points — click to zoom in`;
    return element;
  };

  const sync = () => {
    if (!instance.getSource(sourceId)) return;

    if (!options.isVisible() || instance.getZoom() > config.maxZoom) {
      clear();
      return;
    }

    const features = instance.querySourceFeatures(sourceId, {
      filter: ["has", "point_count"],
    });

    const seen = new Set<number>();

    for (const feature of features) {
      const id = feature.properties?.cluster_id as number;
      if (id === undefined || feature.geometry.type !== "Point") continue;

      seen.add(id);
      if (markers.has(id)) continue;

      const count = String(feature.properties?.point_count_abbreviated ?? "");
      const element = badge(count);
      const coordinates = feature.geometry.coordinates as [number, number];

      element.addEventListener("click", () => {
        const source = instance.getSource(sourceId) as GeoJSONSource;
        source
          .getClusterExpansionZoom(id)
          .then((zoom) => instance.easeTo({ center: coordinates, zoom }))
          .catch(() => instance.easeTo({ center: coordinates, zoom: instance.getZoom() + 2 }));
      });

      markers.set(id, new Marker({ element }).setLngLat(coordinates).addTo(instance));
    }

    for (const [id, marker] of markers) {
      if (!seen.has(id)) {
        marker.remove();
        markers.delete(id);
      }
    }
  };

  instance.on("moveend", sync);
  instance.on("sourcedata", (event) => {
    if (event.sourceId === sourceId) sync();
  });

  return { sync, clear };
}
