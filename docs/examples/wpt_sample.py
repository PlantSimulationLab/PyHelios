"""
WeberPennTree Sample

Builds procedural trees and inspects their geometry:

1. Querying trunk / branch / leaf primitives separately
2. Controlling mesh detail with the resolution setters

The UUID accessors return lists of primitive IDs, which for a mature tree run to
tens of thousands of entries. This example reports their sizes rather than
printing the lists themselves; use the returned UUIDs to assign primitive data,
apply textures, or pull results out of a simulation.

Run:
    python docs/examples/wpt_sample.py
"""

from pyhelios import Context, WeberPennTree, WPTType


def describe(wpt, tree_id, label):
    """Report the primitive breakdown of one tree."""
    trunk = wpt.getTrunkUUIDs(tree_id)
    branch = wpt.getBranchUUIDs(tree_id)
    leaf = wpt.getLeafUUIDs(tree_id)
    everything = wpt.getAllUUIDs(tree_id)

    print(f"{label} (tree_id {tree_id}):")
    print(f"  trunk primitives:  {len(trunk):>7,}")
    print(f"  branch primitives: {len(branch):>7,}")
    print(f"  leaf primitives:   {len(leaf):>7,}")
    print(f"  all primitives:    {len(everything):>7,}")

    # The three groups partition getAllUUIDs() -- no primitive belongs to two
    # groups, and together they account for every primitive in the tree.
    partitions = set(trunk) | set(branch) | set(leaf)
    print(f"  trunk+branch+leaf == all: {partitions == set(everything)}")

    # A sample of actual UUIDs, to show what the accessors return.
    print(f"  first 5 leaf UUIDs: {leaf[:5]}")
    return everything


def main():
    print("WeberPennTree Sample")
    print("=" * 46)

    # --- A tree at the library's default detail settings ---
    context = Context()
    wpt = WeberPennTree(context)

    lemon_id = wpt.buildTree(WPTType.LEMON)
    describe(wpt, lemon_id, "Lemon, default detail")
    print()

    # --- The same species at reduced detail ---
    #
    # These setters apply to trees built AFTER the call, so the lemon above is
    # unaffected. Each controls a different part of the mesh:
    #   setBranchRecursionLevel     -- how many orders of branching are generated
    #   setTrunkSegmentResolution   -- cross-section facets around the trunk
    #   setBranchSegmentResolution  -- cross-section facets around each branch
    #   setLeafSubdivisions         -- mesh cells per leaf (raises leaf count)
    coarse_context = Context()
    coarse_wpt = WeberPennTree(coarse_context)
    coarse_wpt.setBranchRecursionLevel(3)
    coarse_wpt.setTrunkSegmentResolution(3)
    coarse_wpt.setBranchSegmentResolution(3)
    coarse_wpt.setLeafSubdivisions(3, 3)

    coarse_id = coarse_wpt.buildTree(WPTType.LEMON)
    describe(coarse_wpt, coarse_id, "Lemon, reduced detail")
    print()

    print("Coarser trunk/branch resolution lowers the trunk and branch counts,")
    print("while setLeafSubdivisions(3, 3) splits each leaf into a 3x3 mesh and")
    print("therefore raises the leaf count.")
    print()

    # --- A second species, to show the enum ---
    pistachio_id = wpt.buildTree(WPTType.PISTACHIO)
    describe(wpt, pistachio_id, "Pistachio, default detail")
    print()
    # Both the lemon and the pistachio were built into `context`; the reduced
    # detail tree lives in its own Context.
    print(f"Context now holds {context.getPrimitiveCount():,} primitives "
          f"across 2 trees (lemon + pistachio).")


if __name__ == "__main__":
    main()
