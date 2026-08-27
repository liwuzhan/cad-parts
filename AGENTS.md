# Agent instructions

## Part discovery

- Read `CATALOG.md` first or call `cadparts search`; never discover parts by recursively listing source files.
- Use `search → compare → describe → instantiate` so only the selected family enters the context window.
- Treat generated geometry as an assembly proxy unless its declaration explicitly promises higher fidelity.
- Use named interfaces from `cadparts.instance/v2`; do not infer connection frames from screenshots or STEP geometry.
- If no exact item matches, report the closest candidates and unmet constraints. Never invent a designation or dimension.

## Contributions

- Every generator needs a declaration under `src/cadparts/data/catalog/<category>/`.
- Regenerate `src/cadparts/data/catalog/index.json` with `cadparts build-index`.
- Run `cadparts validate-catalog --build-samples`, `pytest -q`, and a multimodal `cadparts review` before committing.
- Do not commit virtual environments, caches, generated STEP/STL/PNG files, standards documents, or vendor CAD files without a compatible license.
