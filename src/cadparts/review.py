"""Reproducible STEP/PNG review artifacts for multimodal contributors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from build123d import export_step

from .catalog import describe, instantiate, list_families
from .errors import CatalogDataError, ReviewError
from .metadata import build_catalog_index, load_catalog_index, load_manifests


STANDARD_VIEWS = {
    "iso": (25, -45),
    "front": (0, -90),
    "right": (0, 0),
    "top": (90, -90),
}


def validate_catalog(
    *,
    check_index: bool = True,
    build_samples: bool = False,
    all_items: bool = False,
) -> dict[str, Any]:
    """Validate declarations, generator coverage and optionally generated geometry."""

    manifests = load_manifests()
    registered = {item["family"] for item in list_families()}
    declared = {str(item["id"]) for item in manifests}
    missing_declarations = sorted(registered - declared)
    missing_generators = sorted(declared - registered)
    if missing_declarations or missing_generators:
        raise CatalogDataError(
            "catalog/generator mismatch; "
            f"missing declarations={missing_declarations}, missing generators={missing_generators}"
        )

    parameter_drift = [
        str(manifest["id"])
        for manifest in manifests
        if describe(str(manifest["id"]))["parameters"] != manifest["parameters"]
    ]
    if parameter_drift:
        raise CatalogDataError(
            "declared parameters drift from the generator contract; "
            f"run `cadparts describe <family>` and sync the declaration: {parameter_drift}"
        )

    generated = build_catalog_index(manifests)
    if check_index and generated != load_catalog_index():
        raise CatalogDataError("catalog index is stale; run `cadparts build-index`")

    samples: list[dict[str, Any]] = []
    if build_samples:
        for manifest in manifests:
            instance = instantiate(str(manifest["id"]), **dict(manifest["sample"]["params"]))
            if not instance.spec["shape"]["valid"]:
                raise CatalogDataError(f"{manifest['id']}: sample shape is invalid")
            samples.append({
                "family": manifest["id"],
                "solid_count": instance.spec["shape"]["solid_count"],
                "interface_count": len(instance.interfaces),
                "envelope": instance.spec["envelope"],
            })

    items: list[dict[str, Any]] = []
    if all_items:
        for entry in generated["entries"]:
            if entry.get("kind") != "item":
                continue
            item_id = str(entry["id"])
            instance = instantiate(item_id)
            shape = instance.spec["shape"]
            items.append({
                "id": item_id,
                "valid": bool(shape["valid"]),
                "solid_count": shape["solid_count"],
                "envelope": instance.spec["envelope"],
            })
        invalid = [item["id"] for item in items if not item["valid"]]
        if invalid:
            listed = ", ".join(invalid[:10])
            raise CatalogDataError(
                f"{len(invalid)} catalog items generate invalid geometry: {listed}"
            )
    return {
        "schema": "cadparts.catalog-validation/v1",
        "family_count": len(manifests),
        "entry_count": len(generated["entries"]),
        "categories": generated["categories"],
        "index_current": True,
        "samples": samples,
        **({"items_checked": len(items)} if all_items else {}),
    }


def _render_shape(shape: Any, interfaces: list[dict[str, Any]], output: Path, view: str) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    except ImportError as exc:
        raise ReviewError("PNG review requires the optional `review` dependency") from exc

    if view not in STANDARD_VIEWS:
        raise ReviewError(f"unknown review view {view!r}; available: {', '.join(STANDARD_VIEWS)}")
    vertices, triangles = shape.tessellate(0.08)
    if not vertices or not triangles:
        raise ReviewError("shape tessellation returned no triangles")
    points = [(point.X, point.Y, point.Z) for point in vertices]
    faces = [[points[index] for index in triangle] for triangle in triangles]

    figure = plt.figure(figsize=(7.2, 5.4), dpi=120)
    axis = figure.add_subplot(111, projection="3d")
    mesh = Poly3DCollection(
        faces,
        facecolor="#e7ebef",
        edgecolor="#27313a",
        linewidth=0.18,
        alpha=1.0,
    )
    axis.add_collection3d(mesh)
    bbox = shape.bounding_box()
    bounds = (
        (bbox.min.X, bbox.max.X),
        (bbox.min.Y, bbox.max.Y),
        (bbox.min.Z, bbox.max.Z),
    )
    centers = [(low + high) / 2 for low, high in bounds]
    span = max(high - low for low, high in bounds) or 1.0
    radius = span * 0.58
    axis.set_xlim(centers[0] - radius, centers[0] + radius)
    axis.set_ylim(centers[1] - radius, centers[1] + radius)
    axis.set_zlim(centers[2] - radius, centers[2] + radius)
    axis.set_box_aspect((1, 1, 1))
    axis.set_proj_type("ortho")

    arrow_length = span * 0.16
    for interface in interfaces:
        frame = interface.get("frame", {})
        origin = frame.get("origin_mm")
        direction = frame.get("axis")
        if not origin or not direction:
            continue
        axis.quiver(
            *origin,
            *(component * arrow_length for component in direction),
            color="#e53935",
            linewidth=1.5,
            arrow_length_ratio=0.22,
        )

    elevation, azimuth = STANDARD_VIEWS[view]
    axis.view_init(elev=elevation, azim=azimuth)
    axis.set_axis_off()
    axis.set_title(f"{shape.label} · {view}", fontsize=10)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, bbox_inches="tight", pad_inches=0.08, facecolor="white")
    plt.close(figure)


def review_part(
    identifier: str,
    *,
    parameters: dict[str, Any] | None = None,
    selections: dict[str, Any] | None = None,
    output_dir: Path,
    views: Iterable[str] = ("iso", "front", "right", "top"),
) -> dict[str, Any]:
    """Build one proxy and emit everything a multimodal reviewer needs."""

    instance = instantiate(identifier, selections=selections, **(parameters or {}))
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = instance.catalog_id.replace(".", "-")
    step_path = output_dir / f"{safe_name}.step"
    spec_path = output_dir / f"{safe_name}.instance.json"
    export_step(instance.shape, step_path)
    spec_path.write_text(
        json.dumps(instance.spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    images: list[dict[str, str]] = []
    for view in views:
        png_path = output_dir / f"{safe_name}.{view}.png"
        _render_shape(instance.shape, instance.interfaces, png_path, view)
        images.append({"view": view, "path": str(png_path.resolve())})
    report = {
        "schema": "cadparts.review/v1",
        "catalog_id": instance.catalog_id,
        "family": instance.spec["family"],
        "valid": instance.spec["shape"]["valid"],
        "solid_count": instance.spec["shape"]["solid_count"],
        "interface_count": len(instance.interfaces),
        "envelope": instance.spec["envelope"],
        "artifacts": {
            "step": str(step_path.resolve()),
            "instance_spec": str(spec_path.resolve()),
            "images": images,
        },
        "review_questions": [
            "Does the proxy visually match the declared part type?",
            "Are the envelope and openings consistent across all views?",
            "Do the red interface axes originate on the intended connection features?",
            "Are omitted manufacturing details clearly declared in the family metadata?",
        ],
    }
    report_path = output_dir / "review.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report["report"] = str(report_path.resolve())
    return report


def review_catalog(
    *,
    output_dir: Path,
    views: Iterable[str] = ("iso",),
) -> dict[str, Any]:
    """Generate a representative review bundle for every declared family."""

    output_dir.mkdir(parents=True, exist_ok=True)
    reports: list[dict[str, Any]] = []
    selected_views = tuple(views)
    for manifest in load_manifests():
        family = str(manifest["id"])
        report = review_part(
            family,
            parameters=dict(manifest["sample"]["params"]),
            output_dir=output_dir / family.replace(".", "-"),
            views=selected_views,
        )
        reports.append({
            "catalog_id": report["catalog_id"],
            "valid": report["valid"],
            "interface_count": report["interface_count"],
            "report": report["report"],
        })
    summary = {
        "schema": "cadparts.catalog-review/v1",
        "family_count": len(reports),
        "views": list(selected_views),
        "all_valid": all(item["valid"] for item in reports),
        "parts": reports,
    }
    summary_path = output_dir / "catalog-review.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary["report"] = str(summary_path.resolve())
    return summary
