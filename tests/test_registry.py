"""The registry's own invariants."""

from thessmap import registry


def test_layer_ids_are_unique():
    ids = [layer.id for layer in registry.LAYERS]
    assert len(ids) == len(set(ids))


def test_every_detail_names_a_real_parent():
    for layer in registry.LAYERS:
        if layer.parent is None:
            continue
        assert layer.parent in registry.SPEC, f"{layer.id} -> {layer.parent}"


def test_a_parent_is_never_itself_a_detail():
    for layer in registry.LAYERS:
        if layer.parent is None:
            continue
        assert registry.SPEC[layer.parent].parent is None, layer.id


def test_every_theme_is_declared():
    for layer in registry.LAYERS:
        assert layer.theme in registry.THEMES, layer.id


def test_zoom_ranges_are_ordered():
    for layer in registry.LAYERS:
        if layer.min_zoom is None or layer.max_zoom is None:
            continue
        assert layer.min_zoom < layer.max_zoom, layer.id


def test_a_detail_stays_inside_its_parents_range():
    for layer in registry.LAYERS:
        parent = registry.SPEC.get(layer.parent or "")
        if parent is None or parent.min_zoom is None or layer.min_zoom is None:
            continue
        assert layer.min_zoom >= parent.min_zoom, layer.id


def test_exclusive_groups_name_real_layers():
    for group in registry.EXCLUSIVE:
        for layer_id in group:
            assert layer_id in registry.SPEC, layer_id


def test_pinned_layers_are_parents():
    for layer_id in registry.PINNED:
        assert registry.SPEC[layer_id].parent is None, layer_id


def test_auto_hiding_layers_are_parents_and_on_by_default():
    for layer_id in registry.AUTO_HIDE:
        layer = registry.SPEC[layer_id]
        assert layer.parent is None, layer_id
        # A layer that is off at the overview has nothing to auto-hide
        assert layer.show, layer_id


def test_groups_are_declared():
    for layer in registry.LAYERS:
        if layer.group is None:
            continue
        assert layer.group in registry.GROUPS, layer.id


def test_the_menu_invents_nothing_and_hides_nothing():
    in_menu = set()

    for entries in registry.menu().values():
        for entry in entries:
            if entry["kind"] == "layer":
                in_menu.add(entry["layer"].id)
            else:
                in_menu.update(layer.id for layer in entry["layers"])

    switchable = {layer.id for layer in registry.PARENTS if not layer.pinned}

    assert in_menu == switchable


def test_pinned_layers_stay_out_of_the_menu():
    shown = set()

    for entries in registry.menu().values():
        for entry in entries:
            if entry["kind"] == "layer":
                shown.add(entry["layer"].id)
            else:
                shown.update(layer.id for layer in entry["layers"])

    assert shown.isdisjoint(registry.PINNED)
