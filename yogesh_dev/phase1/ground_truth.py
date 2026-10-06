"""
T1.1 -- Enable optional plant-architecture object data (plantID/fruitID/leafID/
rank/age/phenology_stage), verified empirically to actually appear.

T1.2 -- Export per-fruit ground truth (fruit_ground_truth.json): object ID,
plantID, centroid, bounding box, equivalent diameter, surface area, primitive
UUID list.

IMPORTANT ORDERING GOTCHA (discovered empirically, not assumed -- see
PHASE1_LOG.md "T1.1" section for the actual A/B test and its output):
`optionalOutputObjectData(...)` must be called on the `PlantArchitecture`
instance BEFORE `buildPlantInstanceFromLibrary()`. The task doc's own
snippet says "After building the plants: plantarch.optionalOutputObjectData(...)"
-- that ordering was tested directly and produces **zero** object data on
every field (`listObjectData` returns `[]` on every fruit object). This
matches the C++ source (`PlantArchitecture.cpp`): the `output_object_data`
flags are read once, at the moment each phytomer/fruit-bud object is
constructed during growth advancement inside `buildPlantInstanceFromLibrary`,
not retroactively. Calling it first (right after `PlantArchitecture(context)`,
before any `loadPlantModelFromLibrary`/`buildPlantInstanceFromLibrary` call)
is what actually works.

A second gotcha (also empirical, not in the task doc): `plantID` is only
written by the plant-architecture model onto internode/petiole/leaf compound
objects, NOT onto fruit objects -- a real fruit object's `listObjectData`
only ever contains `['age', 'fruitID', 'phenology_stage', 'rank']`, never
`plantID`. So `fruit_ground_truth.json`'s `plant_id` field is derived here
by cross-referencing each fruit object's primitive UUIDs against each
tree's `plantarch.getAllPlantUUIDs(plant_id)` set (built once as a
uuid->plant_id lookup), not by reading a `plantID` object-data field off
the fruit object itself.
"""

import json
import math

OPTIONAL_OBJECT_DATA_LABELS = ["plantID", "fruitID", "leafID", "rank", "age", "phenology_stage"]

# Object-data fields empirically confirmed present on fruit objects once
# optionalOutputObjectData is enabled *before* building (see module docstring).
# plantID is deliberately excluded -- it is never set on fruit objects.
# Types (from helios-core's PlantArchitecture.cpp, not assumed): fruitID is
# int (objID cast to int), rank is uint, age is float, phenology_stage is a
# std::string (e.g. "fruit-set") -- NOT an int as the field name might
# suggest. `Context.getObjectData()` (no explicit data_type) auto-detects
# the actual stored type, so a fixed getter-name dispatch table isn't used.
FRUIT_OBJECT_DATA_FIELDS = ["fruitID", "rank", "age", "phenology_stage"]


def enable_fruit_object_data(plantarch, labels=None):
    """T1.1: call BEFORE building any plant instance on this plantarch."""
    if labels is None:
        labels = OPTIONAL_OBJECT_DATA_LABELS
    plantarch.optionalOutputObjectData(list(labels))
    return list(labels)


def verify_object_data_on_fruit(context, fruit_objs, expected_labels=None):
    """T1.1 verification: check `context.listObjectData(objID)` on a REAL fruit
    object and report which expected labels actually appear. Does not assume;
    returns a report dict meant to be logged verbatim.
    """
    if expected_labels is None:
        expected_labels = ["fruitID", "rank", "age", "phenology_stage"]
    if not fruit_objs:
        return {"checked_object_id": None, "labels_present": [], "all_expected_present": False,
                "note": "no fruit objects existed to check"}

    oid = fruit_objs[0]
    labels_present = context.listObjectData(oid)
    all_present = all(lbl in labels_present for lbl in expected_labels)
    return {
        "checked_object_id": oid,
        "labels_present": list(labels_present),
        "expected_labels": list(expected_labels),
        "all_expected_present": all_present,
    }


def equivalent_diameter_from_surface_area(surface_area):
    """Diameter of a sphere with the same surface area: SA = pi * D^2 -> D = sqrt(SA/pi)."""
    if surface_area <= 0:
        return 0.0
    return math.sqrt(surface_area / math.pi)


def build_uuid_to_plant_map(plantarch, plant_ids):
    """uuid -> plant_id lookup, built once from each tree's own primitive set."""
    uuid_to_plant = {}
    for pid in plant_ids:
        for u in plantarch.getAllPlantUUIDs(pid):
            uuid_to_plant[u] = pid
    return uuid_to_plant


def export_fruit_ground_truth(context, plantarch, plant_ids, output_path):
    """T1.2: find every fruit compound object across all trees and write
    `fruit_ground_truth.json` with one record per fruit.

    Returns (fruit_records, report) where report includes counts useful for
    the log (n_fruit_primitives, n_fruit_objects, n_trees).
    """
    uuid_to_plant = build_uuid_to_plant_map(plantarch, plant_ids)
    all_uuids = list(uuid_to_plant.keys())

    fruit_uuids = context.filterPrimitivesByData(all_uuids, "object_label", "fruit")
    fruit_uuid_set = set(fruit_uuids)
    fruit_objs = context.getUniquePrimitiveParentObjectIDs(fruit_uuids, include_zero=False)

    records = []
    plant_id_misses = 0
    for oid in fruit_objs:
        obj_uuids = context.getObjectPrimitiveUUIDs(oid)
        obj_fruit_uuids = [u for u in obj_uuids if u in fruit_uuid_set]
        if not obj_fruit_uuids:
            # Object has no fruit-labeled primitives (shouldn't happen for an
            # object that came from filtering fruit UUIDs) -- skip rather than
            # silently report a zero-area fruit.
            continue

        center = context.getObjectCenter(oid)
        bbox_min, bbox_max = context.getObjectBoundingBox(oid)
        surface_area = sum(context.getPrimitiveArea(u) for u in obj_fruit_uuids)
        diameter = equivalent_diameter_from_surface_area(surface_area)

        plant_id = uuid_to_plant.get(obj_fruit_uuids[0])
        if plant_id is None:
            plant_id_misses += 1

        record = {
            "object_id": oid,
            "plant_id": plant_id,
            "centroid": [center.x, center.y, center.z],
            "bbox_min": [bbox_min.x, bbox_min.y, bbox_min.z],
            "bbox_max": [bbox_max.x, bbox_max.y, bbox_max.z],
            "equivalent_diameter_m": diameter,
            "surface_area_m2": surface_area,
            "primitive_uuids": [int(u) for u in obj_fruit_uuids],
        }
        for field in FRUIT_OBJECT_DATA_FIELDS:
            if context.doesObjectDataExist(oid, field):
                record[field] = context.getObjectData(oid, field)
        records.append(record)

    with open(output_path, "w") as f:
        json.dump(records, f, indent=2)

    report = {
        "n_fruit_primitives": len(fruit_uuids),
        "n_fruit_objects": len(fruit_objs),
        "n_fruit_records_written": len(records),
        "n_trees": len(plant_ids),
        "plant_id_lookup_misses": plant_id_misses,
        "output_path": output_path,
    }
    return records, report
