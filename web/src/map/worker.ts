import { setWorkerUrl } from "maplibre-gl";
// `?worker&url` so Vite bundles it. MapLibre resolves the worker with a
// runtime-computed URL no bundler can follow, and plain `?url` copies a
// file whose own sibling import is never emitted — both leave the built
// map with a basemap and no layers.
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";

setWorkerUrl(workerUrl);
