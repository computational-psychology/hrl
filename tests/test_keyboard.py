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
        (pygame.K_KP_PLUS, "+"),
        (pygame.K_KP_MINUS, "-"),
        (pygame.K_KP_MULTIPLY, "*"),
        (pygame.K_KP_DIVIDE, "/"),
        (pygame.K_KP_PERIOD, "."),
        (pygame.K_KP_EQUALS, "="),
        (pygame.K_KP_ENTER, "Enter"),
    ],
)
def test_keymap_keypad_symbol(key, name):
    assert keyMap(key) == name


@pytest.mark.parametrize(
    "key, name",
    [
        (pygame.K_PLUS, "+"),
        (pygame.K_MINUS, "-"),
        (pygame.K_ASTERISK, "*"),
        (pygame.K_SLASH, "/"),
        (pygame.K_PERIOD, "."),
        (pygame.K_EQUALS, "="),
        (pygame.K_RETURN, "Enter"),
    ],
)
def test_keymap_main_keyboard_symbol(key, name):
    assert keyMap(key) == name


def test_keymap_symbol_names_are_the_characters_they_represent():
    # The name of a symbol key is the character pygame associates with it
    for key in (
        pygame.K_PLUS,
        pygame.K_MINUS,
        pygame.K_ASTERISK,
        pygame.K_SLASH,
        pygame.K_PERIOD,
        pygame.K_EQUALS,
    ):
        assert keyMap(key) == chr(key)


def test_keymap_keypad_and_main_keyboard_names_coincide():
    pairs = [
        (getattr(pygame, f"K_{d}"), getattr(pygame, f"K_KP{d}")) for d in range(10)
    ]
    pairs += [
        (pygame.K_PLUS, pygame.K_KP_PLUS),
        (pygame.K_MINUS, pygame.K_KP_MINUS),
        (pygame.K_ASTERISK, pygame.K_KP_MULTIPLY),
        (pygame.K_SLASH, pygame.K_KP_DIVIDE),
        (pygame.K_PERIOD, pygame.K_KP_PERIOD),
        (pygame.K_EQUALS, pygame.K_KP_EQUALS),
        (pygame.K_RETURN, pygame.K_KP_ENTER),
    ]
    for main_key, keypad_key in pairs:
        assert keyMap(main_key) == keyMap(keypad_key)
        assert keyMap(main_key) is not None


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


def test_checkkey_filters_symbols():
    btns = ("+", "-", "Enter")
    assert checkKey(pygame.K_KP_PLUS, btns) == "+"
    assert checkKey(pygame.K_MINUS, btns) == "-"
    assert checkKey(pygame.K_KP_ENTER, btns) == "Enter"
    assert checkKey(pygame.K_KP_MULTIPLY, btns) is None
    assert checkKey(pygame.K_5, btns) is None


def test_keymap_backspace():
    assert keyMap(pygame.K_BACKSPACE) == "Backspace"


def test_checkkey_filters_backspace():
    btns = ("1", "2", "Backspace")
    assert checkKey(pygame.K_BACKSPACE, btns) == "Backspace"
    assert checkKey(pygame.K_BACKSPACE, ("1", "2")) is None
