import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

import build_global


class NormalizationTests(unittest.TestCase):
    def test_minmax_handles_all_missing_and_constant_series(self):
        missing = build_global.minmax_100(pd.Series([np.nan, np.nan]))
        constant = build_global.minmax_100(pd.Series([7.0, np.nan, 7.0]))
        self.assertTrue(missing.isna().all())
        self.assertEqual(constant.tolist()[0], 50.0)
        self.assertTrue(np.isnan(constant.tolist()[1]))
        self.assertEqual(constant.tolist()[2], 50.0)

    def test_composite_renormalizes_when_complexity_is_missing(self):
        frame = pd.DataFrame(
            {
                "M_china": [1_000_000.0, 10_000_000.0, 100_000_000.0],
                "M_world": [10_000_000.0, 20_000_000.0, 100_000_000.0],
                "PCI": [np.nan, 0.0, 1.0],
            }
        )
        scored = build_global.score_country(frame)
        expected = (
            scored.loc[0, "zD"] * build_global.DEFAULT_WEIGHTS[0]
            + scored.loc[0, "zS"] * build_global.DEFAULT_WEIGHTS[1]
        ) / build_global.DEFAULT_WEIGHTS[:2].sum()
        self.assertAlmostEqual(scored.loc[0, "CPS"], expected)
        self.assertTrue(np.isnan(scored.loc[0, "SOPH"]))
        self.assertTrue(scored["D"].between(0, 1).all())


class AggregationTests(unittest.TestCase):
    def test_duckdb_matches_published_missing_year_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            year_2022 = root / "BACI_HS22_Y2022_Vtest.csv"
            year_2023 = root / "BACI_HS22_Y2023_Vtest.csv"
            year_2022.write_text(
                "t,i,j,k,v,q\n"
                "2022,156,1,010101,10,1\n"
                "2022,200,1,010101,90,1\n"
                "2022,200,1,020202,40,1\n",
                encoding="utf-8",
            )
            year_2023.write_text(
                "t,i,j,k,v,q\n"
                "2023,156,1,010101,30,1\n"
                "2023,200,1,010101,70,1\n"
                "2023,156,1,020202,20,1\n",
                encoding="utf-8",
            )
            result = build_global.aggregate_trade([year_2022, year_2023], 156).set_index("hs6")

        self.assertEqual(result.loc["010101", "M_world"], 100_000.0)
        self.assertEqual(result.loc["010101", "M_china"], 20_000.0)
        self.assertEqual(result.loc["020202", "M_world"], 30_000.0)
        # No China row in 2022 is missing, not an imputed zero: parity with the
        # original published pandas aggregation.
        self.assertEqual(result.loc["020202", "M_china"], 20_000.0)


if __name__ == "__main__":
    unittest.main()
