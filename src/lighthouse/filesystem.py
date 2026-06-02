from pathlib import Path


def ignore_in_git(path) -> Path:
    """Add a .gitignore to the path if it's not already there."""
    path = Path(path)
    path.mkdir(exist_ok=True, parents=True)
    if not (path / ".gitignore").exists():
        (path / ".gitignore").write_text("*\n")
    return path
