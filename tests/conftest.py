import pytest


def pytest_addoption(parser):
    """Add custom command-line options for pytest."""
    parser.addoption(
        "--photometer-dev",
        action="store",
        default="/dev/ttyUSB0",
        help="Device path for photometer (default: /dev/ttyUSB0)",
    )


@pytest.fixture
def photometer_dev(request):
    """Get the photometer device path from command-line or use default.

    Can be overridden with: pytest --photometer-dev=/dev/ttyUSB1
    """
    return request.config.getoption("--photometer-dev")
