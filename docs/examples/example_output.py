"""
Shared output-directory helper for the PyHelios examples.

Examples that write files (images, movies, XML, text exports) put them under
``docs/examples/output/<name>/`` rather than the current working directory, so
running an example never scatters files across the project root. Everything an
example produces can be removed with:

    rm -rf docs/examples/output
"""

from pathlib import Path

# Root of the PyHelios source tree (docs/examples/example_output.py -> up 3).
REPO_ROOT = Path(__file__).resolve().parents[2]

# Root for all example-generated files (gitignored).
OUTPUT_ROOT = REPO_ROOT / "docs" / "examples" / "output"


def get_output_dir(name: str) -> Path:
    """
    Return the output directory for an example, creating it if needed.

    Args:
        name: Subdirectory name, normally the example's own name.

    Returns:
        Path to ``docs/examples/output/<name>/``.
    """
    output_dir = OUTPUT_ROOT / name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def display_path(path) -> str:
    """
    Format a path for printing.

    Paths inside the PyHelios source tree print relative to its root
    (``docs/examples/output/...``); anything else, such as a user-supplied
    output directory, prints as an absolute path.
    """
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)
