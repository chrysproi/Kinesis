import { setWorkerUrl } from "maplibre-gl";
// `?worker&url` makes Vite *bundle* the worker and hand back its final
// path. Plain `?url` copies the file verbatim, and the copy still
// imports "./maplibre-gl-shared.mjs" — a sibling Vite never emits, so
// the worker 404s inside itself where nothing on the page can see it.
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";

/**
 * Points MapLibre at its worker explicitly.
 *
 * MapLibre resolves the worker itself with `new URL(name, import.meta.url)`
 * where `name` is chosen at runtime between the dev and production
 * builds. A bundler cannot follow a computed specifier, so nothing is
 * emitted and the built app requests a file that was never written —
 * a 404 the dev server never shows, because there the module graph is
 * served from source.
 *
 * The failure is silent: the map, the controls and the basemap all
 * appear, and only the layers the worker parses are missing.
 */
setWorkerUrl(workerUrl);
