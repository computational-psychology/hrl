import pytest

from hrl.graphics import ALIASES, GREY_ALIASES, RGB_ALIASES, gpu, new_graphics


def test_aliases_is_union_of_grey_and_rgb():
    assert len(ALIASES) == len(GREY_ALIASES) + len(RGB_ALIASES)
    assert set(ALIASES) == set(GREY_ALIASES) | set(RGB_ALIASES)


def test_aliases_unique_ignoring_case():
    # Case-insensitive lookup is only well defined if no two keys differ just by case
    lowered = [alias.lower() for alias in ALIASES]
    assert len(lowered) == len(set(lowered))


@pytest.mark.graphics
@pytest.mark.parametrize("alias", ["gpu", "Grey", "GRAY", "gpu_grey", "GPU_GREY", "Gpu_Grey"])
def test_resolve_alias_gpu_variants(alias):
    graphics = new_graphics(graphics_alias=alias, width=200, height=200)
    assert isinstance(graphics, gpu.GPU_grey)


@pytest.mark.graphics
@pytest.mark.parametrize("alias", ["gpu_RGB", "gpu_rgb", "GPU_RGB", "Gpu_Rgb", "RGB", "rgb"])
def test_resolve_alias_gpu_rgb_variants(alias):
    graphics = new_graphics(graphics_alias=alias, width=200, height=200)
    assert isinstance(graphics, gpu.GPU_RGB)


@pytest.mark.graphics
def test_unknown_alias_raises_before_opening_window():
    with pytest.raises(ValueError, match="Unknown graphics device"):
        new_graphics(graphics_alias="notadevice", width=200, height=200)


@pytest.mark.graphics
def test_error_lists_valid_options():
    with pytest.raises(ValueError) as excinfo:
        new_graphics(graphics_alias="notadevice", width=200, height=200)
    for alias in ALIASES:
        assert alias in str(excinfo.value)
