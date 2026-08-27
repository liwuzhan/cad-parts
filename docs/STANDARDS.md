# Dimensional source policy

`cad-parts` stores the nominal dimensions and interface metadata needed for an
assembly proxy. Sources may be a standard, a manufacturer drawing, a product
datasheet or an explicitly identified common commercial series. The repository
does not redistribute standards documents or proprietary vendor CAD files.

A generated solid is not a claim that a manufactured part complies with
dimensional tolerances, material, process, grade, strength, marking or
inspection requirements.

## Source hierarchy

1. Official issuing-body catalog or full-text service for standardized series.
2. Current ISO standard when a GB/T document is an adoption or equivalent.
3. Official standards-body scope page for paid ASME/AGMA/ASTM publications.
4. Manufacturer dimension drawing or datasheet for a manufacturer/series item.
5. A documented common commercial-series reference when no governing standard
   exists; the proxy must then say that the dimensions are series-specific.

Every table or formula must record the source, checked date and whether the
relationship is governing, equivalent, series-specific, similar or
nominal-envelope only. Two visually similar vendor products must not be merged
unless their assembly-critical interfaces were verified identical.

## Baseline references checked 2026-08-27

| Domain | Chinese / ISO basis | United States basis | Library use |
|---|---|---|---|
| Deep-groove bearings | [GB/T 276-2013](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=E58A2862B90502BB3A7EF18F835504BD), [ISO 15:2017](https://www.iso.org/standard/69977.html) | ABMA boundary-dimension series (to be verified per family) | Nominal d/D/B table and simplified geometry |
| Metric hex screws | [GB/T 5783-2025 official notice](https://openstd.samr.gov.cn/bzgk/std/nd?no=2561), [ISO 4017:2022](https://www.iso.org/standard/72585.html) | ASME B18 metric/inch series kept as separate specs | Nominal head, shank and thread-envelope geometry |
| Metric regular nuts | [GB/T 6170-2015](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=BDDE5AF77AC2FBC2D194289F10C69A4B), [ISO 4032:2023](https://www.iso.org/standard/75016.html) | ASME B18 inch nuts are a separate family | Nominal hex envelope and thread-envelope bore |
| Inch hex bolts | — | [ASME B18.2.1](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws) | Inch-series dimensional table |
| Inch nuts | — | [ASME B18.2.2-2022](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts) | Inch-series dimensional table |
| Washers | [GB/T 97.1-2002](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=199E0585386FDF8B9CACF6225BA5F924), [ISO 7089:2000](https://www.iso.org/standard/13666.html) | [ASME B18.21.1](https://www.asme.org/codes-standards/find-codes-standards/b18-21-1-washers-helical-spring-lock-tooth-lock-plain-washers) | Plain-washer envelope |
| Cylindrical gears | [GB/T 1356-2001](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=7D44A15888B2E686063491408AB63CC8), [ISO 53:1998](https://www.iso.org/standard/22643.html) (confirmed 2026) | ANSI/AGMA geometry and tolerance families | Involute reference profile; strength rating is out of scope |
| Fine-pitch gears | ISO 53 relationship | [ANSI/AGMA 1003-H07](https://members.agma.org/ItemDetail?Category=STANDARDS&WebsiteKey=1fa29655-e8c0-41f6-b6a8-418a374ae587&iProductCode=1003_H07) | Explicit scope guard for fine pitch |
| Straight bevel gears | [GB/T 12369-1990](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=27174F3824CCFC3370B47C1DA0B89314), [ISO 23509-1:2025](https://www.iso.org/standard/85503.html) | [ANSI/AGMA ISO 23509-B17](https://members.agma.org/MyAGMA/MyAGMA/Store/Item_Detail.aspx?Category=STANDARDS&iProductCode=23509_B17) | Pitch-cone macro geometry; scaled-section layout model only |
| Structural hollow sections | [GB/T 6728-2025](https://openstd.samr.gov.cn/bzgk/std/showGb?hcno=D2862F3B35CBDC75C7262BEAEE5B47FD&request_locale=zh&type=online) | [ASTM A500/A500M-23](https://store.astm.org/a0500_a0500m-23.html) | User-specified nominal section envelope |
| Hot-rolled equal angles | [GB/T 706-2016](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=80EC2383403568E9F0F850B044C0DC5F) | ASTM shape families require separate licensed dimensional data | Explicit leg/thickness sharp envelope |
| Parallel keys | [GB/T 1096-2003](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=AF989792A444C725A4F3FFB90F183772) | [ASME B17.1-1967 (S2023)](https://www.asme.org/codes-standards/find-codes-standards/b17-1-keys-keyseats) | Explicit b×h×L and end form; no keyway/tolerance |

## Edition handling

- Standards are immutable references: a family points to an explicit edition.
- A superseding edition is added before the old one is removed.
- Existing API defaults change only in a documented minor release.
- Deprecated editions remain selectable when reproducibility requires them.
