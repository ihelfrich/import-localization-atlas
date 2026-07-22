# Import Localization Atlas

**Author:** Dr. Ian Helfrich ([ihelfrich](https://github.com/ihelfrich), ianthelfrich@gmail.com)

A global, interactive instrument that classifies **any country's imports from China** at the
six-digit (HS6) product level, and ranks products for domestic localization by import
dependence, import scale, and economic complexity, placing each in a four-quadrant typology.

## Open the atlas

**[ihelfrich.github.io/import-localization-atlas](https://ihelfrich.github.io/import-localization-atlas/)**

Pick an importing country, then move the weight sliders and watch the ranking recompute live
in your browser. Runs entirely client-side (no server), lazy-loading one country at a time.

## Method, in short

For each product a country imports:

1. **Import dependence** on China (China's share of the country's imports of that product).
2. **Import scale** (dollar value, the exposure magnitude).
3. **Economic complexity** (OEC Product Complexity Index, bridged across HS vintages).

These are normalized and combined into a composite score, and each product is placed on a
two-axis map: China exposure versus economic complexity. The upper-right quadrant (high
dependence, high complexity, material value) is the localization shortlist.

The ranking rests on the dimensions computable from hard public data. Three further dimensions
of the full framework (domestic value added, ESG, policy alignment) need country-specific data
and are documented as inputs rather than invented.

## Positioning and prior work

This is a **synthesis-and-application** contribution: a single-country, whole-import-basket HS6
instrument for localization prioritization. It builds openly on established methods and does not
claim to originate them: trade-dependence and Herfindahl concentration measures; revealed
comparative advantage (Balassa 1965); economic complexity and the product space (Hidalgo &
Hausmann 2009; Hidalgo, Klinger, Barabasi & Hausmann 2007); and the dependence-versus-capability
framing used in recent supply-chain-resilience work (Cresti et al. 2025; European Commission
2021). Two extensions are developed separately in a working paper: a **value-chain-completion
index** (the share of an imported good's inputs the country already exports competitively) and a
**reverse-dependence round-trip screen** (products a country exports as feedstock and reimports
as finished goods). © 2026 Ian Helfrich.

## Data

| Data | Source | Licence |
|---|---|---|
| Bilateral trade, HS6, 2022-2023 | CEPII BACI (HS22, V202601) | Etalab 2.0 |
| Product Complexity Index | Observatory of Economic Complexity | per OEC terms |
| HS2022 nomenclature | UN Comtrade H6 reference | UN |

## Reproduce

`build_global.py` builds every country's data from the BACI bulk file; `build_global_tool.py`
generates the tool. Python 3 with `pandas` and `numpy`.
