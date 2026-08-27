"""Language-model-friendly parametric standard parts for build123d."""

from ._version import __version__
from .catalog import (
    compare,
    create,
    derive,
    describe,
    describe_part,
    get_family,
    instance_spec,
    instantiate,
    list_families,
    search,
)
from .bearings import deep_groove_bearing, deep_groove_dimensions
from .fasteners import (
    hex_bolt_metric,
    hex_bolt_metric_dimensions,
    hex_nut_metric,
    hex_nut_metric_dimensions,
    plain_washer_metric,
    plain_washer_metric_dimensions,
)
from .gears import (
    spur_gear,
    spur_gear_dimensions,
    straight_bevel_gear,
    straight_bevel_gear_dimensions,
)
from .keys import parallel_key, parallel_key_dimensions
from .models import FamilyDefinition, ParameterSpec, PartInstance, StandardReference
from .profiles import (
    equal_angle,
    equal_angle_dimensions,
    round_rod,
    round_rod_dimensions,
    round_tube,
    round_tube_dimensions,
    square_tube,
    square_tube_dimensions,
)

__all__ = [
    "FamilyDefinition",
    "ParameterSpec",
    "PartInstance",
    "StandardReference",
    "compare",
    "create",
    "deep_groove_bearing",
    "deep_groove_dimensions",
    "derive",
    "describe",
    "describe_part",
    "equal_angle",
    "equal_angle_dimensions",
    "get_family",
    "hex_bolt_metric",
    "hex_bolt_metric_dimensions",
    "hex_nut_metric",
    "hex_nut_metric_dimensions",
    "instance_spec",
    "instantiate",
    "list_families",
    "parallel_key",
    "parallel_key_dimensions",
    "plain_washer_metric",
    "plain_washer_metric_dimensions",
    "round_rod",
    "round_rod_dimensions",
    "round_tube",
    "round_tube_dimensions",
    "search",
    "square_tube",
    "square_tube_dimensions",
    "spur_gear",
    "spur_gear_dimensions",
    "straight_bevel_gear",
    "straight_bevel_gear_dimensions",
]
