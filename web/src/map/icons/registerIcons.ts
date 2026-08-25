/** Registering the sprites with MapLibre as rasters. */

import type { Map as MapLibreMap } from "maplibre-gl";

import {
  ICON_SPRITES,
  RASTER_ICONS,
  type IconSprite,
} from "../../generated/layerRegistry";
import { BUILT, SVG } from "./sprites";

const RASTER_SCALE = 2;

function colorise(svg: string, color: string, size: number) {
  const px = size * RASTER_SCALE;

  return svg
    .replace(/currentColor/g, color)
    .replace(/(<svg[^>]*?)\swidth="\d+"/, `$1 width="${px}"`)
    .replace(/(<svg[^>]*?)\sheight="\d+"/, `$1 height="${px}"`);
}

function rasterise(sprite: IconSprite): Promise<ImageData> {
  const built = BUILT[sprite.lucide];
  const svg = built ? built(sprite.color) : SVG[sprite.lucide];

  if (!svg) {
    return Promise.reject(
      new Error(
        `No SVG imported for lucide icon "${sprite.lucide}" (sprite ` +
          `"${sprite.id}"). Add it to SVG in src/map/icons.ts.`,
      ),
    );
  }

  const px = sprite.size * RASTER_SCALE;
  const markup = built
    ? svg.replace("<svg", `<svg width="${px}" height="${px}"`)
    : colorise(svg, sprite.color, sprite.size);
  const url = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(markup)}`;

  return new Promise((resolve, reject) => {
    const image = new Image(px, px);

    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = px;
      canvas.height = px;

      const context = canvas.getContext("2d");
      if (!context) {
        reject(new Error("No 2d context available for icon rasterising"));
        return;
      }

      context.drawImage(image, 0, 0, px, px);
      resolve(context.getImageData(0, 0, px, px));
    };

    image.onerror = () =>
      reject(new Error(`Could not decode SVG for sprite "${sprite.id}"`));

    image.src = url;
  });
}

/** Supplied artwork, which keeps its own colours. */
function loadArtwork(file: string): Promise<ImageData> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;
      const context = canvas.getContext("2d");
      if (!context) return reject(new Error(`No 2D context for ${file}`));
      context.drawImage(image, 0, 0);
      resolve(context.getImageData(0, 0, canvas.width, canvas.height));
    };
    image.onerror = () => reject(new Error(`Could not load artwork ${file}`));
    image.src = `${import.meta.env.BASE_URL}${file}`;
  });
}

export async function loadIcons(map: MapLibreMap) {
  const loaded = await Promise.all(
    ICON_SPRITES.map(async (sprite) => {
      try {
        return [sprite, await rasterise(sprite)] as const;
      } catch (error) {
        console.error(error);
        return null;
      }
    }),
  );

  for (const entry of loaded) {
    if (!entry) continue;
    const [sprite, bitmap] = entry;
    if (map.hasImage(sprite.id)) continue;
    map.addImage(sprite.id, bitmap, { pixelRatio: RASTER_SCALE });
  }

  await Promise.all(
    Object.entries(RASTER_ICONS).map(async ([id, file]) => {
      if (map.hasImage(id)) return;
      try {
        map.addImage(id, await loadArtwork(file), { pixelRatio: 2 });
      } catch (error) {
        console.error(error);
      }
    }),
  );
}
