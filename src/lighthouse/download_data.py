from pathlib import Path
from activitysim.cli.create import download_asset
import platformdirs


def default_cache_dir() -> Path:
    """
    Get the default external example cache directory.

    Returns
    -------
    Path
    """
    return Path(platformdirs.user_cache_dir(appname="ActivitySim")).joinpath(
        "External-Examples"
    )


def mtc_full(where: Path = Path.cwd()):
    """Get the MTC full data and link it to the target location."""
    url = "https://github.com/ActivitySim/activitysim-prototype-mtc/releases/download/v1.3.4/data_full.tar.zst"
    download_asset(
        url,
        Path(url).name,
        sha256="b402506a61055e2d38621416dd9a5c7e3cf7517c0a9ae5869f6d760c03284ef3",
        link=default_cache_dir(),
        base_path=str(where),
        unpack="data_full",
    )
