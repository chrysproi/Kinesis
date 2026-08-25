"""The contract between Python, the generated module and the shipped data.

These are the tests that catch drift rather than bugs: a layer renamed
in the registry but not re-exported, an icon referenced with no sprite,
a source with no file behind it.
"""

import json
import re

from thessmap import config, registry, webexport

WEB = config.PROJECT_ROOT / "web"
GENERATED = WEB / "src" / "generated" / "layerRegistry.ts"
DATA = WEB / "public" / "data"


def emitted(name):
    """
    One exported const from the generated module, as Python data.

    Brackets are matched rather than pattern-matched: the values nest,
    and a non-greedy regex stops at the first closing bracket inside
    them, which parses as truncated JSON rather than failing loudly.
    """
    text = GENERATED.read_text()
    match = re.search(rf"export const {name}(?::[^=]+)? =\s*", text)
    assert match, f"{name} missing from {GENERATED.name}"

    start = match.end()
    opening = text[start]
    closing = {"[": "]", "{": "}"}[opening]

    depth, index, in_string = 0, start, False
    while index < len(text):
        char = text[index]
        if in_string:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                break
        index += 1

    return json.loads(text[start:index + 1])


def test_generated_module_is_up_to_date():
    """Regenerating changes nothing — the committed file matches the source."""
    before = GENERATED.read_text()
    webexport.write_layers_ts(GENERATED, verbose=False)
    assert GENERATED.read_text() == before, (
        "layerRegistry.ts is stale — run scripts/export_web_data.py --types-only"
    )


def test_every_map_layer_names_a_real_toggle():
    toggles = {layer["id"] for layer in emitted("TOGGLE_LAYERS")}

    for layer in emitted("MAP_LAYERS"):
        parent = layer["metadata"]["thessmap:parent"]
        assert parent in toggles, f"{layer['id']} -> {parent}"


def test_every_source_has_a_file():
    for name in emitted("SOURCE_NAMES"):
        assert (DATA / f"{name}.json").is_file(), name


def test_no_orphan_data_files():
    """Nothing shipped that the map never asks for."""
    sources = set(emitted("SOURCE_NAMES"))
    rasters = {
        raster["url"] for raster in emitted("RASTER_SOURCES").values()
    }

    for path in DATA.iterdir():
        if path.suffix == ".json":
            assert path.stem in sources, path.name
        else:
            assert path.name in rasters, path.name


def icon_names(image):
    """
    The sprite ids an `icon-image` value can resolve to.

    A match expression is ["match", input, key, value, key, value, …,
    fallback]: the sprites are the *values* and the fallback. Taking
    every string would also collect the keys, which are feature property
    values like "Regular Stop" and name no sprite at all.
    """
    if isinstance(image, str):
        return [image]
    if not isinstance(image, list) or image[0] != "match":
        return []

    return [image[index] for index in range(3, len(image) - 1, 2)] + [image[-1]]


def test_every_icon_reference_has_a_sprite():
    sprites = {sprite["id"] for sprite in emitted("ICON_SPRITES")}
    artwork = set(emitted("RASTER_ICONS"))

    seen = 0
    for layer in emitted("MAP_LAYERS"):
        image = (layer.get("layout") or {}).get("icon-image")
        if image is None:
            continue

        for name in icon_names(image):
            seen += 1
            assert name in sprites or name in artwork, f"{layer['id']}: {name}"

    assert seen > 0, "no icon-image found — the test is checking nothing"


def test_every_legend_block_points_at_a_drawn_layer():
    toggles = {layer["id"] for layer in emitted("TOGGLE_LAYERS")}

    for key, block in emitted("LEGEND").items():
        named = (
            [block.get("layer")]
            + list(block.get("anyOf") or [])
            + [entry.get("layer") for entry in block.get("entries") or []]
        )
        for layer_id in filter(None, named):
            assert layer_id in toggles, f"{key} -> {layer_id}"

        assert block["theme"] in registry.THEMES, key


def test_every_switchable_layer_has_a_legend():
    """A switch that draws something the reader cannot look up is a gap."""
    keyed = set()

    for block in emitted("LEGEND").values():
        keyed.add(block.get("layer"))
        keyed.update(block.get("anyOf") or [])
        keyed.update(
            entry.get("layer") for entry in block.get("entries") or []
        )

    for layer in emitted("TOGGLE_LAYERS"):
        if layer["id"] in registry.PINNED:
            continue
        assert layer["id"] in keyed, layer["id"]


def test_exclusive_groups_and_pinned_layers_survive_export():
    toggles = {layer["id"] for layer in emitted("TOGGLE_LAYERS")}

    for group in emitted("EXCLUSIVE_GROUPS"):
        for layer_id in group:
            assert layer_id in toggles, layer_id

    for layer_id in emitted("PINNED_LAYERS"):
        assert layer_id in toggles, layer_id


def test_lazy_sources_are_real_sources():
    sources = set(emitted("SOURCE_NAMES"))
    for name in emitted("LAZY_SOURCES"):
        assert name in sources, name
