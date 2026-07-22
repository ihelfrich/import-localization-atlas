# Import Localization Atlas

**Author:** Dr. Ian Helfrich ([ihelfrich](https://github.com/ihelfrich),
ianthelfrich@gmail.com)

The Import Localization Atlas is a client-side instrument for classifying any included
country's imports from China at the six-digit HS2022 product level. It combines import
dependence, import scale, and product complexity into an adjustable ranking, then places each
product in a four-quadrant localization typology.

## Open the atlas

**[ihelfrich.github.io/import-localization-atlas](https://ihelfrich.github.io/import-localization-atlas/)**

The atlas has no server-side component, external scripts, fonts, analytics, or API calls. It
loads a compact country index and one local country JSON file at a time. Current features
include:

- exact, adjustable scoring weights and decision thresholds;
- a decision map, sortable and filterable product ranking, and HS2 chapter drill-down;
- country search, keyboard-accessible controls, responsive layouts, and dark mode;
- URL hashes that preserve the country, weights, thresholds, and active filters;
- a downloadable CSV of every product in the current filtered view; and
- explicit PCI coverage/provenance and an unclassified state for products with missing PCI.

## Method

For product `p` in an importing country:

1. **Dependence** `D_p` is imports from China divided by imports from the world, bounded to
   `[0, 1]`.
2. **Scale** is `log10(imports from China in USD)`.
3. **Complexity** is the OEC Product Complexity Index (PCI), bridged from HS2012 to HS2022 by
   an exact HS6 match where available and then by an HS4 fallback.

Each available indicator is winsorized at the country's 1st and 99th percentiles and min-max
normalized to 0–100. A constant non-null indicator maps to 50. The composite priority score is
the weighted mean over available indicators:

```text
CPS = sum(weight_i * normalized_i) / sum(weight_i for available indicators)
```

The documented defaults are dependence `0.417`, scale `0.250`, and complexity `0.333`.
Missing PCI therefore does not discard a product from the CPS ranking. It does, however,
prevent an honest high/low-complexity classification, so the web tool marks that product
`U · Missing PCI`.

The two map axes are:

```text
EXPOSURE       = 0.6 * normalized dependence + 0.4 * normalized scale
SOPHISTICATION = normalized complexity
```

With the default inclusive thresholds of 60:

| Priority | Exposure | Sophistication | Interpretation |
|---|---:|---:|---|
| A · Localize | high | high | Strong first-screen localization candidate |
| B · Diversify | high | low | Reduce or diversify concentrated exposure |
| C · Watch | low | high | Sophisticated product worth monitoring |
| D · Low | low | low | Lower priority on these measured dimensions |
| U · Missing PCI | any | unavailable | Ranked on available inputs, not assigned to a quadrant |

The material shortlist is quadrant A with China imports strictly greater than $5 million.
Equality with either map threshold counts as high.

## Scope and interpretation

This is a **synthesis-and-application** contribution: a whole-import-basket HS6 instrument for
localization prioritization. It builds on established trade-dependence, concentration,
revealed-comparative-advantage, economic-complexity, product-space, and supply-chain-resilience
methods. The two-axis typology is not claimed as novel.

The ranking uses only dimensions computable consistently from hard public data. Domestic
value added, ESG, and policy alignment require country-specific evidence and remain documented
inputs rather than fabricated values. Treat quadrant A as a first screen, not an investment
recommendation or feasibility study.

The novel **value-chain-completion index** and **reverse-dependence round-trip screen** are
separate working-paper extensions and are not represented by the data in this atlas.

Suggested citation:

> Helfrich, Ian (2026), *Import Localization Atlas*.

## Data and averaging

| Data | Source | Licence / terms |
|---|---|---|
| Bilateral trade, HS6, 2022–2023 | CEPII BACI, HS22 V202601 | Etalab 2.0 |
| Product Complexity Index | Observatory of Economic Complexity | OEC terms |
| HS2022 product names and chapters | UN Comtrade H6 reference | UN terms |

BACI values are reported in thousands of USD. The atlas takes the arithmetic mean over years
in which BACI reports a positive flow. BACI does not contain explicit zero-flow rows, and the
published series does not impute an absent row as zero. This convention is retained for
backward comparability and is stated in the tool.

Countries enter the atlas when their average imports from China reach $200 million and at
least 30 HS6 products have positive China imports. HS2 chapter dependence in the browser covers
the HS6 products with observed China imports; zero-China products are not included in the lazy
country payload. The country-level China share shown in the KPI uses the full world-import
basket.

## Repository layout

- `build_global.py` scans and aggregates BACI with DuckDB, applies country-relative scoring,
  and writes `docs/data/<ISO3>.json` plus `docs/index.json`.
- `build_global_tool.py` generates the single, dependency-free `docs/index.html`, including a
  hash-based Content Security Policy for its inline CSS and JavaScript.
- `chapter_names.json`, `hs6_codes.csv`, `pci_hs6.csv`, and `pci_hs4_fallback.csv` provide local
  nomenclature and complexity references.
- `tests/` covers aggregation semantics, missing-data normalization, generated HTML integrity,
  CSP hashes, and JavaScript syntax.

The compact country record schema is:

```text
[hs6, name, chapter2, China_$m_display, dependence_pct, PCI,
 zDependence, zScale, zComplexity, EXPOSURE, SOPHISTICATION, material,
 world_$m_precise, pci_bridge_source, China_$m_precise]
```

Fields 0–11 preserve the original published schema and rounding. `pci_bridge_source` is `6`
for an exact HS6 bridge, `4` for an HS4 fallback, and `0` when unavailable. The precise trade
fields support accurate browser aggregation and CSV export without changing legacy values.

## Reproduce and test

Python 3.10 or newer is recommended.

The generated public data are tracked, but the large `baci/` bulk directory and the local
`pci_hs6.csv` / `pci_hs4_fallback.csv` bridge inputs are intentionally gitignored. A full
rebuild therefore requires those source files to be present alongside the tracked support
files; ordinary use of the published atlas does not.

```bash
python3 -m pip install -r requirements.txt
python3 build_global.py
python3 build_global_tool.py
python3 -m unittest discover -s tests -v
```

For a faster parity check that writes outside the published directories:

```bash
python3 build_global.py \
  --countries DEU SAU USA \
  --output-dir /tmp/atlas-sample/data \
  --index-file /tmp/atlas-sample/index.json
```

To preview locally, serve `docs/` over HTTP; browser security normally prevents `fetch()` from
working when `index.html` is opened directly as a `file://` URL.

```bash
python3 -m http.server --directory docs 8000
```

The default build deliberately remains on 2022–2023 even if newer BACI files are present,
because changing the time window would create a new data vintage rather than a code-only
improvement. Pass `--years` explicitly to conduct a separate, clearly versioned build.

© 2026 Ian Helfrich.
