import type { StyleSpecification } from "maplibre-gl";

const ATTRIBUTION =
  '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ' +
  '© <a href="https://carto.com/attributions">CARTO</a>';

const TILES = "https://a.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png";

/**
 * A minimal, label-free raster basemap. Swapping this for a vector
 * basemap later changes nothing about how the thematic layers are added.
 */
export function basemapStyle(): StyleSpecification {
  return {
    version: 8,
    sources: {
      basemap: {
        type: "raster",
        tiles: [TILES],
        tileSize: 256,
        attribution: ATTRIBUTION,
      },
    },
    layers: [{ id: "basemap", type: "raster", source: "basemap" }],
  };
}
