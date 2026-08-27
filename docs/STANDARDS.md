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
| Square stepper motors | Common frame classes checked against [Oriental Motor frame-size guidance](https://www.orientalmotor.com/stepper-motors/stepper-motor-frame-sizes.html) | NEMA-like names remain search aliases, not universal interchangeability claims | Frame, pilot, bolt pattern and shaft planning evidence |
| IEC rotating machines | [IEC 60072-1:2022](https://webstore.iec.ch/en/publication/67088) | NEMA frames require a separate family | Shaft height and B3/B5/B14/B35 interface basis |
| Right-angle gearboxes | NMRV range checked against the [Motovario VSF/NMRV series](https://www.motovario.com/eng/products/worm-gear-reducers--vsf-series/worm-gear-reducers-combined-and-with-pre-stage-reduction-unit) | BKM is retained as a distinct market series | Nominal market-series envelope and I/O interface evidence; verify vendor drawing before substitution |
| Profile linear guides | [HIWIN linear-guide product families](https://hiwin.com/products/linear-guideways/) | Other makers may use similar but not identical names | MGN/MGW/HGR/HGW planning profiles, rail holes and carriage sweep |
| Ball screws/supports | [HIWIN ballscrew and support families](https://hiwin.com/products/ballscrews-supports/) | Finished shaft ends remain product-specific | SFU screw/nut and BK/BF/EK/EF/FK/FF planning profiles |
| Roller-chain sprockets | [ISO 606:2015](https://www.iso.org/standard/61232.html) | ANSI chain series require separate tables | Pitch-circle and chain-plane planning geometry |
| Small-bore pneumatic cylinders | [ISO 6432:2015](https://www.iso.org/standard/66468.html) | — | Nominal bore and mounting-interface basis; accessories remain catalog-specific |
| Detachable-mount pneumatic cylinders | [ISO 15552:2018](https://www.iso.org/standard/72672.html) | — | Nominal profile and mounting-interface basis |
| Compact pneumatic cylinders | [ISO 21287:2004](https://www.iso.org/standard/32705.html) | SDA is documented separately as a market family | Compact envelope and interface basis; do not equate SDA with ISO by name |

## Compatibility claims

Every manifest declares one of these levels:

| Level | Meaning |
|---|---|
| `normative` | A cited standard governs the stated interface basis. Product options outside that scope still need checking. |
| `cross_vendor_verified` | Assembly-critical fields were compared across more than one vendor source. The fields are listed in `match_fields`. |
| `series_compatible` | A common market series or nominal frame narrows procurement. It is not a blanket interchangeability claim. |
| `catalog_specific` | Dimensions describe one catalog or explicit parameter set; no automatic substitution is claimed. |

The claim is intentionally returned with every search result and generated instance. A model should compare the listed
`match_fields` before replacing one product with another and should preserve unresolved options in the BOM description.

## Edition handling

- Standards are immutable references: a family points to an explicit edition.
- A superseding edition is added before the old one is removed.
- Existing API defaults change only in a documented minor release.
- Deprecated editions remain selectable when reproducibility requires them.
