"""
Interactive check of keyboard input in HRL.

Opens a small window and prints the name of every recognized key that is
pressed (arrows, Space, Enter, Backspace, digits and keypad symbols), together
with the time since readButton was called. Unrecognized keys are ignored.
Press Escape to quit.

Usage:
    python examples/example_keyboard_input.py

"""

from hrl import HRL

EXPECTED_KEYS = (
    "Up Down Left Right Space Enter Backspace "
    "0 1 2 3 4 5 6 7 8 9 + - * / . ="
)


def open_window():
    return HRL(
        graphics="gpu",
        inputs="keyboard",
        photometer=None,
        wdth=400,
        hght=300,
        bg=0.5,
        db=True,
        fs=False,
        lut=None,
    )


def format_press(btn, t):
    return f"pressed {btn!r} after {t:.3f} s"


def run(ihrl):
    print("Press keys in the HRL window. Recognized keys:")
    print(EXPECTED_KEYS)
    print("Press Escape to quit.")
    while True:
        btn, t = ihrl.inputs.readButton()
        print(format_press(btn, t))
        if btn == "Escape":
            break


if __name__ == "__main__":
    ihrl = open_window()
    ihrl.graphics.flip()
    try:
        run(ihrl)
    finally:
        ihrl.close()
