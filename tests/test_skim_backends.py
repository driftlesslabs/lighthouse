"""Actual skim lookups must respect zone IDs with either execution backend."""

from pathlib import Path
import sys
import uuid

import activitysim.abm  # noqa: F401
from activitysim.core import workflow
import numpy as np
import openmatrix as omx
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
import extensions  # noqa: E402, F401 -- register runtime setup used by the CLI


@pytest.mark.parametrize("sharrow", [False, "require"])
def test_unsorted_omx_ids_and_directional_periods(tmp_path, sharrow):
    config = tmp_path / "configs"
    data = tmp_path / "data"
    config.mkdir()
    data.mkdir()
    # Three distinct orders: source land use, sorted IDs, and OMX storage.
    pd.DataFrame({"zone_id": [30, 10, 20]}).to_csv(data / "land_use.csv", index=False)
    raw = np.array(
        [[2020, 2030, 2010], [3020, 3030, 3010], [1020, 1030, 1010]], dtype=np.float32
    )
    with omx.open_file(str(data / "skims.omx"), "w") as skims:
        skims["dist_nm"] = raw
        skims["time__AM"] = raw + 10000
        skims["time__PM"] = raw + 20000
        skims.create_mapping("ID", [20, 30, 10])
    (config / "settings.yaml").write_text(
        yaml.safe_dump(
            {
                "inherit_settings": True,
                "multiprocess": False,
                "input_table_list": [
                    {
                        "tablename": "land_use",
                        "filename": "land_use.csv",
                        "index_col": "zone_id",
                        "recode_columns": {"zone_id": "zero-based"},
                    }
                ],
            }
        )
    )
    (config / "network_los.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "test_" + uuid.uuid4().hex,
                "zone_system": 1,
                "taz_skims": ["skims.omx"],
                "skim_time_periods": {
                    "period_minutes": 60,
                    "time_window": 1440,
                    "periods": [0, 12, 24],
                    "labels": ["AM", "PM"],
                },
            }
        )
    )
    configs = [config]
    if sharrow:
        configs.append(ROOT / "model/configs_sh")
    configs.append(ROOT / "model/configs")
    state = workflow.State.make_default(
        configs_dir=configs, data_dir=data, output_dir=tmp_path / "output"
    )
    assert state.settings.sharrow == sharrow
    assert state.settings.recode_pipeline_columns == bool(sharrow)
    land_use = state.get_dataframe("land_use")
    mapping = (
        dict(zip(land_use["_original_zone_id"], land_use.index))
        if sharrow
        else {i: i for i in land_use.index}
    )
    skim = state.get_injectable("network_los").get_default_skim_dict()
    origins = np.array([mapping[30], mapping[10]])
    destinations = np.array([mapping[10], mapping[20]])
    np.testing.assert_array_equal(
        skim.lookup(origins, destinations, "dist_nm"), [3010, 1020]
    )
    frame = pd.DataFrame(
        {"origin": origins, "destination": destinations, "period": ["AM", "PM"]}
    )
    wrapper = skim.wrap_3d("origin", "destination", "period")
    wrapper.set_df(frame)
    np.testing.assert_array_equal(wrapper["time"], [13010, 21020])
