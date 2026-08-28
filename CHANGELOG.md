# Changelog

All notable catalog, interface and parameter-contract changes are recorded here.

## Unreleased

- Family declarations now persist their full `parameters` contract; `validate-catalog` and the manifest loader reject declarations whose parameters drift from the registered generator.
- Added `cadparts validate-catalog --all-items` to instantiate and BRep-validate every catalog entry instead of one sample per family.
- Inline planetary items now declare the complete input/output interface dimensions (`output_flange_diameter`, pilots, hole pitches, `output_shaft_diameter`/`_length`) used by `compatibility.match_fields`; the legacy `output_shaft` key was replaced by the canonical name.
- CATALOG.md now states that timing-pulley and chain-sprocket geometry are tooth-less pitch envelopes where `teeth` only sets the pitch diameter.

## 0.2.0 — 2026-08-27

- Expanded the catalog to 34 families and 288 concrete model/specification entries.
- Added stepper, servo and IEC motors plus market right-angle and inline planetary gearboxes.
- Added mounted bearings, flexible couplings, linear guides, ball screws, support units, linear bushings, timing pulleys, chain sprockets and taper-lock bushes.
- Added ISO and market-series pneumatic cylinders, electric actuators, proximity sensors, axial fans, leveling feet and industrial casters.
- Added explicit compatibility levels, match fields and advisory motion/service keepouts to the instance contract.
- Improved Chinese/English multi-term search so a specific purchased item outranks its family declaration.
- Aligned support-unit and caster mounting-hole geometry with their named interface evidence.

## 0.1.0 — 2026-08-27

- Added a model-first catalog with a fixed `CATALOG.md` entry point and generated JSON index.
- Added 11 parametric proxy families and 22 concrete 62/63-series deep-groove bearing entries.
- Added deterministic `search`, `compare`, `describe`, `instantiate` and JSON CLI operations.
- Added `cadparts.instance/v2` with purchase selections, exact envelopes and named assembly interfaces.
- Added STEP/PNG multimodal review bundles and catalog contribution validation.
- Added traceable standards/source policy while explicitly excluding manufacturing certification and strength analysis.
