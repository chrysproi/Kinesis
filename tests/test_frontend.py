"""The frontend's structural claims, checked rather than asserted in prose.

Written in Python so one `pytest` covers both halves of the repository;
they read TypeScript as text and never run it.
"""

import re

from thessmap import config, registry

WEB = config.PROJECT_ROOT / "web" / "src"
CONFIG_TS = WEB / "config" / "layerConfig.ts"
GENERATED = WEB / "generated" / "layerRegistry.ts"

# Lower reads higher, never the other way. config and generated are the
# ground the rest is built on; layers is the model; map, sidebar, ui and
# url are the presentation.
DEPTH = {
    "config": 0,
    "generated": 0,
    "layers": 1,
    "map": 2,
    "sidebar": 2,
    "ui": 2,
    "url": 2,
}


def sources():
    return [
        path
        for path in WEB.rglob("*.ts*")
        if path.suffix in {".ts", ".tsx"} and "generated" not in path.parts
    ]


def test_dependencies_never_run_upward():
    violations = []

    for path in sources():
        relative = path.relative_to(WEB)
        area = relative.parts[0] if len(relative.parts) > 1 else None
        if area not in DEPTH:
            continue

        # Both `… from "x"` and the bare side-effect `import "x"`, which
        # crosses a boundary just as thoroughly while matching neither
        # half of a from-clause.
        specs = re.findall(
            r'(?:from|import)\s+"(\.[^"]+)"', path.read_text()
        )

        for spec in specs:
            target = (path.parent / spec).resolve().relative_to(WEB.resolve())
            other = target.parts[0] if len(target.parts) > 1 else None

            if other in DEPTH and DEPTH[other] > DEPTH[area]:
                violations.append(f"{relative} -> {target}")

    assert not violations, "upward imports: " + ", ".join(violations)


def test_nothing_imports_the_generated_module_by_its_old_name():
    for path in sources():
        assert "generated/layers\"" not in path.read_text(), path.name


def test_config_overrides_name_real_layers():
    """A typo in layerConfig.ts is otherwise silent — it just does nothing."""
    text = CONFIG_TS.read_text()
    toggles = {layer.id for layer in registry.PARENTS}
    unknown = []

    for field in ("opacity", "zoom", "theme", "startsOn"):
        block = re.search(rf"\n  {field}: \{{(.*?)\}} as", text, re.S)
        if not block:
            continue
        # Keys outside the doc comment, which carries examples
        body = re.sub(r"/\*.*?\*/", "", block.group(1), flags=re.S)
        unknown += [
            key for key in re.findall(r"^\s*(\w+):", body, re.M)
            if key not in toggles
        ]

    assert not unknown, f"unknown layer ids in layerConfig.ts: {unknown}"


def test_configured_theme_order_names_real_themes():
    text = CONFIG_TS.read_text()
    block = re.search(r"themeOrder: \[(.*?)\] as Theme\[\]", text, re.S)
    named = re.findall(r'"([^"]+)"', block.group(1)) if block else []

    for theme in named:
        assert theme in registry.THEMES, theme


def test_the_generated_module_says_it_is_generated():
    first = GENERATED.read_text().splitlines()[0]
    assert "GENERATED" in first and "do not edit" in first
