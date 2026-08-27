# Contributing to cad-parts

The review question is not “is this a manufacturing-perfect model?” It is:

> Can an agent identify, select, reserve space for, mount and purchase this part without reading its geometry code?

## Required contribution package

Every new family must include:

1. A JSON self-declaration in `src/cadparts/data/catalog/<category>/`.
2. A lightweight build123d generator and a deterministic representative sample.
3. Exact assembly-critical envelope dimensions and named interfaces.
4. Search aliases in the common Chinese and English terminology.
5. Purchase selectors or an order/search designation when applicable.
6. Tests for parameter validation, envelope, interfaces and STEP export.
7. A traceable dimensional source: an issuing-body page, manufacturer drawing,
   product datasheet, or clearly identified common-series reference.
8. An explicit compatibility level and the interface fields that must match.
9. Advisory keepout volumes for motion, swivel, airflow, cabling or service access when relevant.

Internal mechanisms, cosmetic detail, tolerance, material and strength analysis may be omitted when the declaration says so.

## Data and geometry rules

- Do not copy or redistribute standards documents, paid drawings or proprietary CAD files.
- Record only the dimensions and source metadata needed to reproduce the proxy.
- Do not normalize two vendor series into one model unless their assembly interfaces were verified identical.
- Product options that share an envelope, such as bearing closure or clearance,
  should normally be `selection` fields rather than duplicate geometry.
- A missing dimension must remain missing. Never fill it with an unverified model guess.
- Keepouts are review evidence, not automatic pass/fail rules. Do not use them to replace model or human judgment.
- The rendered solid, named interfaces and declaration must tell the same story; a declared hole or shaft must be visible in the representative review unless explicitly abstract.

## Local review

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev,review]'
cadparts build-index
cadparts validate-catalog --build-samples
pytest -q
cadparts review your.family --output-dir build/review
```

The final command emits STEP, instance JSON, standard-view PNG files with interface axes, and `review.json`.
Inspect all views before opening a pull request.

CI rejects missing declarations, stale indexes, invalid samples, failed exports or test regressions and uploads a representative review bundle for multimodal inspection.
