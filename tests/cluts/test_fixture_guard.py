"""Guard test ensuring committed CLUT fixtures match generator output."""

import subprocess
from pathlib import Path


def test_clut_fixtures_up_to_date():
    root = Path(__file__).resolve().parents[2]
    script = root / "tests" / "cluts" / "generate_test_data.py"

    result = subprocess.run(
        ["python", str(script), "--check"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "CLUT fixture files are out of date. "
        "Run `python tests/cluts/generate_test_data.py` to regenerate them.\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
