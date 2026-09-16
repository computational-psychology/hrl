import pytest

from hrl.graphics import ALIASES, GREY_ALIASES, RGB_ALIASES, new_graphics, resolve_alias


@pytest.mark.parametrize("alias", list(ALIASES.keys()))
def test_resolve_alias_documented_spelling(alias):
    assert resolve_alias(alias) == ALIASES[alias]


@pytest.mark.parametrize("alias", list(ALIASES.keys()))
def test_resolve_alias_lowercase(alias):
    assert resolve_alias(alias.lower()) == ALIASES[alias]


@pytest.mark.parametrize("alias", list(ALIASES.keys()))
def test_resolve_alias_uppercase(alias):
    assert resolve_alias(alias.upper()) == ALIASES[alias]


@pytest.mark.parametrize("alias", ["gpu_RGB", "gpu_rgb", "GPU_RGB", "Gpu_Rgb", "RGB", "rgb"])
def test_resolve_alias_gpu_rgb_variants(alias):
    assert resolve_alias(alias) == "gpu.GPU_RGB"


@pytest.mark.parametrize("alias", ["viewpixx_RGB", "viewpixx_rgb", "VIEWPIXX_RGB"])
def test_resolve_alias_viewpixx_rgb_variants(alias):
    assert resolve_alias(alias) == "viewpixx.VIEWPixx_RGB"


def test_aliases_unique_ignoring_case():
    # Case-insensitive lookup is only well defined if no two keys differ just by case
    lowered = [alias.lower() for alias in ALIASES]
    assert len(lowered) == len(set(lowered))


def test_aliases_is_union_of_grey_and_rgb():
    assert len(ALIASES) == len(GREY_ALIASES) + len(RGB_ALIASES)
    assert set(ALIASES) == set(GREY_ALIASES) | set(RGB_ALIASES)


@pytest.mark.parametrize("alias", ["", "gpu_rgba", "rgb ", "notadevice"])
def test_resolve_alias_unknown_raises(alias):
    with pytest.raises(ValueError, match="Unknown graphics device"):
        resolve_alias(alias)


def test_resolve_alias_error_lists_valid_options():
    with pytest.raises(ValueError) as excinfo:
        resolve_alias("notadevice")
    for alias in ALIASES:
        assert alias in str(excinfo.value)


def test_new_graphics_unknown_alias_raises_before_opening_window():
    with pytest.raises(ValueError, match="Unknown graphics device"):
        new_graphics(graphics_alias="notadevice", width=200, height=200)
