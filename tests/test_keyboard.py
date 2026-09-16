import pygame
import pytest

from hrl.inputs.keyboard import checkKey, keyMap

DIGITS = [str(d) for d in range(10)]


@pytest.mark.parametrize("digit", DIGITS)
def test_keymap_top_row_digit(digit):
    assert keyMap(getattr(pygame, f"K_{digit}")) == digit


@pytest.mark.parametrize("digit", DIGITS)
def test_keymap_keypad_digit(digit):
    assert keyMap(getattr(pygame, f"K_KP{digit}")) == digit


def test_keymap_digit_is_parseable_as_int():
    for d in range(10):
        assert int(keyMap(getattr(pygame, f"K_{d}"))) == d


@pytest.mark.parametrize(
    "key, name",
    [
        (pygame.K_UP, "Up"),
        (pygame.K_DOWN, "Down"),
        (pygame.K_LEFT, "Left"),
        (pygame.K_RIGHT, "Right"),
        (pygame.K_SPACE, "Space"),
        (pygame.K_ESCAPE, "Escape"),
    ],
)
def test_keymap_named_keys_unchanged(key, name):
    assert keyMap(key) == name


def test_keymap_unmapped_key_returns_none():
    assert keyMap(pygame.K_a) is None


def test_checkkey_accepts_any_mapped_key_without_filter():
    assert checkKey(pygame.K_7, None) == "7"
    assert checkKey(pygame.K_KP3, None) == "3"


def test_checkkey_filters_digits():
    btns = ("1", "2", "3")
    assert checkKey(pygame.K_2, btns) == "2"
    assert checkKey(pygame.K_KP1, btns) == "1"
    assert checkKey(pygame.K_4, btns) is None
    assert checkKey(pygame.K_SPACE, btns) is None


def test_checkkey_unmapped_key_returns_none():
    assert checkKey(pygame.K_a, None) is None
