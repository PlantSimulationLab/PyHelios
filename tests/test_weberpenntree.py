"""
Tests for PyHelios WeberPennTree module.

These tests verify the WeberPennTree class functionality for procedural tree generation.
"""

import pytest
from unittest.mock import Mock, patch
import pyhelios
from pyhelios import Context, WeberPennTree, WPTType, DataTypes
from tests.test_utils import GeometryValidator, PlatformHelper


@pytest.mark.native_only
class TestWeberPennTreeCreation:
    """Test WeberPennTree creation and basic lifecycle."""
    
    def test_wpt_creation(self, basic_context):
        """Test WeberPennTree creation with Context."""
        wpt = WeberPennTree(basic_context)
        assert wpt is not None
        assert hasattr(wpt, 'wpt')
        assert hasattr(wpt, 'context')
        wpt.__exit__(None, None, None)
    
    def test_wpt_context_manager(self, basic_context):
        """Test WeberPennTree as context manager."""
        with WeberPennTree(basic_context) as wpt:
            assert wpt is not None
    
    def test_wpt_native_ptr_access(self, weber_penn_tree):
        """Test native pointer access."""
        ptr = weber_penn_tree.getNativePtr()
        assert ptr is not None
    
    def test_wpt_requires_context(self):
        """Test that WeberPennTree requires a valid Context."""
        with pytest.raises(TypeError):
            WeberPennTree()  # Missing required context parameter


@pytest.mark.native_only
class TestTreeGeneration:
    """Test tree generation functionality."""
    
    @pytest.mark.parametrize("tree_type", [
        pytest.param('ALMOND', marks=pytest.mark.skipif(WPTType is None, reason="WPTType not available")),
        pytest.param('APPLE', marks=pytest.mark.skipif(WPTType is None, reason="WPTType not available")),
        pytest.param('LEMON', marks=pytest.mark.skipif(WPTType is None, reason="WPTType not available")),
        pytest.param('OLIVE', marks=pytest.mark.skipif(WPTType is None, reason="WPTType not available")),
        pytest.param('PEACH', marks=pytest.mark.skipif(WPTType is None, reason="WPTType not available")),
    ])
    def test_build_basic_trees(self, weber_penn_tree, tree_type):
        """Test building different tree types."""
        # Convert string to WPTType enum
        if WPTType is None:
            pytest.skip("WPTType not available")
        wpt_type = getattr(WPTType, tree_type)
        tree_id = weber_penn_tree.buildTree(wpt_type)
        
        assert isinstance(tree_id, int)
        assert tree_id >= 0  # Valid tree ID
        
        # Validate tree structure
        stats = GeometryValidator.validate_tree_structure(weber_penn_tree, tree_id)
        assert stats['valid'], f"Tree validation failed: {stats.get('error', 'Unknown error')}"
        assert stats['trunk_count'] > 0, "Tree should have trunk segments"
    
    def test_build_tree_with_origin(self, weber_penn_tree):
        """Test building tree with custom origin."""
        origin = DataTypes.vec3(10, 20, 5)
        tree_id = weber_penn_tree.buildTree(WPTType.LEMON, origin=origin)
        
        assert isinstance(tree_id, int)
        assert tree_id >= 0
    
    def test_build_tree_with_scale(self, weber_penn_tree):
        """Test building tree with custom scale."""
        tree_id = weber_penn_tree.buildTree(WPTType.APPLE, scale=2.0)
        
        assert isinstance(tree_id, int)
        assert tree_id >= 0
    
    def test_build_tree_with_all_parameters(self, weber_penn_tree):
        """Test building tree with all parameters."""
        origin = DataTypes.vec3(5, 5, 0)
        scale = 1.5
        tree_id = weber_penn_tree.buildTree(WPTType.WALNUT, origin=origin, scale=scale)
        
        assert isinstance(tree_id, int)
        assert tree_id >= 0


@pytest.mark.native_only
class TestTreeStructureQueries:
    """Test querying tree structure and components."""
    
    def test_getTrunkUUIDs(self, weber_penn_tree):
        """Test getting trunk UUIDs."""
        tree_id = weber_penn_tree.buildTree(WPTType.APPLE)
        trunk_uuids = weber_penn_tree.getTrunkUUIDs(tree_id)
        
        assert isinstance(trunk_uuids, list)
        assert len(trunk_uuids) > 0, "Tree should have trunk segments"
        assert all(isinstance(uuid, int) for uuid in trunk_uuids)
    
    def test_getBranchUUIDs(self, weber_penn_tree):
        """Test getting branch UUIDs."""
        tree_id = weber_penn_tree.buildTree(WPTType.APPLE)
        branch_uuids = weber_penn_tree.getBranchUUIDs(tree_id)
        
        assert isinstance(branch_uuids, list)
        # Branches might be empty for simple trees or low recursion
        assert all(isinstance(uuid, int) for uuid in branch_uuids)
    
    def test_getLeafUUIDs(self, weber_penn_tree):
        """Test getting leaf UUIDs."""
        tree_id = weber_penn_tree.buildTree(WPTType.OLIVE)
        leaf_uuids = weber_penn_tree.getLeafUUIDs(tree_id)
        
        assert isinstance(leaf_uuids, list)
        assert len(leaf_uuids) > 0, "Tree should have leaves"
        assert all(isinstance(uuid, int) for uuid in leaf_uuids)
    
    def test_getAllUUIDs(self, weber_penn_tree):
        """Test getting all tree UUIDs."""
        tree_id = weber_penn_tree.buildTree(WPTType.PISTACHIO)
        
        trunk_uuids = weber_penn_tree.getTrunkUUIDs(tree_id)
        branch_uuids = weber_penn_tree.getBranchUUIDs(tree_id)
        leaf_uuids = weber_penn_tree.getLeafUUIDs(tree_id)
        all_uuids = weber_penn_tree.getAllUUIDs(tree_id)
        
        # All UUIDs should equal sum of components
        expected_total = len(trunk_uuids) + len(branch_uuids) + len(leaf_uuids)
        assert len(all_uuids) == expected_total
        
        # Check for UUID uniqueness
        all_component_uuids = set(trunk_uuids + branch_uuids + leaf_uuids)
        assert len(all_component_uuids) == expected_total, "UUIDs should not overlap"
        
        # Check that all_uuids contains all component UUIDs
        all_uuids_set = set(all_uuids)
        assert all_component_uuids == all_uuids_set

    def test_uuid_getters_prune_deleted_primitives(self, weber_penn_tree, basic_context):
        """Deleted primitives must not be reported by the UUID getters.

        Regression test for helios-core 1.3.80: the plug-in caches the UUIDs it creates at
        build time and never learned about deletions made directly through the Context, so
        deleting tree geometry left the getters handing back dangling UUIDs. Because
        getAllUUIDs() is typically passed straight to another plug-in, that surfaced as a
        "does not exist in the Context" error far from the deletion.
        """
        tree_id = weber_penn_tree.buildTree(WPTType.OLIVE)

        leaf_uuids = weber_penn_tree.getLeafUUIDs(tree_id)
        assert len(leaf_uuids) > 2, "Need several leaves to delete a subset"
        all_before = weber_penn_tree.getAllUUIDs(tree_id)

        deleted = leaf_uuids[:2]
        for uuid in deleted:
            basic_context.deletePrimitive(uuid)

        leaf_after = weber_penn_tree.getLeafUUIDs(tree_id)
        all_after = weber_penn_tree.getAllUUIDs(tree_id)

        for uuid in deleted:
            assert uuid not in leaf_after, f"getLeafUUIDs still returns deleted primitive {uuid}"
            assert uuid not in all_after, f"getAllUUIDs still returns deleted primitive {uuid}"
        assert len(leaf_after) == len(leaf_uuids) - len(deleted)
        assert len(all_after) == len(all_before) - len(deleted)

    def test_invalid_tree_id_queries(self, weber_penn_tree):
        """Test queries with invalid tree ID."""
        invalid_tree_id = 99999

        # Should raise HeliosRuntimeError for invalid tree ID (fail-fast behavior)
        with pytest.raises(pyhelios.exceptions.HeliosRuntimeError, match="Tree ID 99999 does not exist"):
            weber_penn_tree.getTrunkUUIDs(invalid_tree_id)

        with pytest.raises(pyhelios.exceptions.HeliosRuntimeError, match="Tree ID 99999 does not exist"):
            weber_penn_tree.getBranchUUIDs(invalid_tree_id)

        with pytest.raises(pyhelios.exceptions.HeliosRuntimeError, match="Tree ID 99999 does not exist"):
            weber_penn_tree.getLeafUUIDs(invalid_tree_id)

        with pytest.raises(pyhelios.exceptions.HeliosRuntimeError, match="Tree ID 99999 does not exist"):
            weber_penn_tree.getAllUUIDs(invalid_tree_id)


@pytest.mark.native_only
class TestTreeParameterSettings:
    """Test tree parameter configuration."""
    
    def test_setBranchRecursionLevel(self, weber_penn_tree):
        """Test setting branch recursion level."""
        # Test with different recursion levels
        for level in [1, 2, 3, 5]:
            weber_penn_tree.setBranchRecursionLevel(level)
            
            # Build tree and check it has branches (if level > 0)
            tree_id = weber_penn_tree.buildTree(WPTType.APPLE)
            branch_uuids = weber_penn_tree.getBranchUUIDs(tree_id)
            
            if level > 1:
                # Higher recursion should generally produce branches
                # (though exact behavior depends on tree species parameters)
                pass  # Just ensure no exceptions are raised
    
    def test_setTrunkSegmentResolution(self, weber_penn_tree):
        """Test setting trunk segment resolution."""
        for resolution in [3, 5, 10]:
            weber_penn_tree.setTrunkSegmentResolution(resolution)
            
            tree_id = weber_penn_tree.buildTree(WPTType.LEMON)
            trunk_uuids = weber_penn_tree.getTrunkUUIDs(tree_id)
            
            assert len(trunk_uuids) > 0
    
    def test_setBranchSegmentResolution(self, weber_penn_tree):
        """Test setting branch segment resolution."""
        for resolution in [3, 5, 10]:
            weber_penn_tree.setBranchSegmentResolution(resolution)
            
            # Set recursion level to ensure branches
            weber_penn_tree.setBranchRecursionLevel(3)
            tree_id = weber_penn_tree.buildTree(WPTType.WALNUT)
            
            # Just ensure no exceptions
            branch_uuids = weber_penn_tree.getBranchUUIDs(tree_id)
    
    def test_setLeafSubdivisions(self, weber_penn_tree):
        """Test setting leaf subdivisions."""
        test_cases = [(1, 1), (2, 2), (3, 3), (4, 4), (2, 4)]
        
        for x_segs, y_segs in test_cases:
            weber_penn_tree.setLeafSubdivisions(x_segs, y_segs)
            
            tree_id = weber_penn_tree.buildTree(WPTType.OLIVE)
            leaf_uuids = weber_penn_tree.getLeafUUIDs(tree_id)
            
            assert len(leaf_uuids) > 0, "Tree should have leaves"
    
    def test_parameter_combination(self, weber_penn_tree):
        """Test combining multiple parameter settings."""
        # Configure tree with specific parameters
        weber_penn_tree.setBranchRecursionLevel(4)
        weber_penn_tree.setTrunkSegmentResolution(5)
        weber_penn_tree.setBranchSegmentResolution(3)
        weber_penn_tree.setLeafSubdivisions(3, 3)
        
        tree_id = weber_penn_tree.buildTree(WPTType.APPLE)
        
        # Validate the tree structure
        stats = GeometryValidator.validate_tree_structure(weber_penn_tree, tree_id)
        assert stats['valid']
        
        # Should have more complex structure with higher parameters
        assert stats['trunk_count'] > 0
        # Branch and leaf counts depend on species-specific parameters


@pytest.mark.native_only
class TestMultipleTreeGeneration:
    """Test generating multiple trees."""
    
    def test_multiple_trees_same_type(self, weber_penn_tree):
        """Test generating multiple trees of the same type."""
        tree_ids = []
        
        for i in range(3):
            origin = DataTypes.vec3(i * 10, 0, 0)  # Space trees apart
            tree_id = weber_penn_tree.buildTree(WPTType.LEMON, origin=origin)
            tree_ids.append(tree_id)
        
        # All trees should have unique IDs
        assert len(set(tree_ids)) == 3
        
        # Each tree should have valid structure
        for tree_id in tree_ids:
            stats = GeometryValidator.validate_tree_structure(weber_penn_tree, tree_id)
            assert stats['valid']
    
    def test_multiple_trees_different_types(self, weber_penn_tree):
        """Test generating multiple trees of different types."""
        tree_types = [WPTType.ALMOND, WPTType.APPLE, WPTType.LEMON, WPTType.OLIVE]
        tree_ids = []
        
        for i, tree_type in enumerate(tree_types):
            origin = DataTypes.vec3(i * 15, 0, 0)
            tree_id = weber_penn_tree.buildTree(tree_type, origin=origin)
            tree_ids.append(tree_id)
        
        assert len(set(tree_ids)) == len(tree_types)
        
        # Verify each tree
        for tree_id in tree_ids:
            stats = GeometryValidator.validate_tree_structure(weber_penn_tree, tree_id)
            assert stats['valid']


class TestWeberPennTreeMocking:
    """Test WeberPennTree with mocked dependencies."""
    
    def test_mock_wpt_basic_operations(self, mock_weber_penn_tree):
        """Test basic operations with mocked WeberPennTree."""
        tree_id = mock_weber_penn_tree.buildTree(WPTType.LEMON)
        assert tree_id == 1
        
        trunk_uuids = mock_weber_penn_tree.getTrunkUUIDs(tree_id)
        assert trunk_uuids == [1, 2, 3]
        
        all_uuids = mock_weber_penn_tree.getAllUUIDs(tree_id)
        assert len(all_uuids) == 9
    
    def test_mock_wpt_parameter_settings(self, mock_weber_penn_tree):
        """Test parameter settings with mocked WeberPennTree."""
        # These should not raise exceptions
        mock_weber_penn_tree.setBranchRecursionLevel(3)
        mock_weber_penn_tree.setTrunkSegmentResolution(5)
        mock_weber_penn_tree.setBranchSegmentResolution(3)
        mock_weber_penn_tree.setLeafSubdivisions(4, 4)


@pytest.mark.unit
class TestWPTTypeEnum:
    """Test WPTType enumeration."""
    
    def test_wpt_type_values(self):
        """Test that WPTType enum has expected values."""
        if WPTType is None:
            pytest.skip("WPTType not available")
            
        expected_types = [
            'ALMOND', 'APPLE', 'AVOCADO', 'LEMON', 'OLIVE', 
            'ORANGE', 'PEACH', 'PISTACHIO', 'WALNUT'
        ]
        
        for type_name in expected_types:
            assert hasattr(WPTType, type_name)
            wpt_type = getattr(WPTType, type_name)
            assert isinstance(wpt_type.value, str)
    
    @pytest.mark.skipif(WPTType is None, reason="WPTType not available")
    @pytest.mark.parametrize("tree_type_name", [
        'ALMOND', 'APPLE', 'AVOCADO', 'LEMON',
        'OLIVE', 'ORANGE', 'PEACH', 'PISTACHIO', 'WALNUT'
    ])
    def test_wpt_type_enum_values(self, tree_type_name):
        """Test individual WPTType enum values."""
        if WPTType is None:
            pytest.skip("WPTType not available")
        tree_type = getattr(WPTType, tree_type_name)
        assert isinstance(tree_type.value, str)
        assert tree_type.value.isalpha()  # Should be alphabetic string
        assert tree_type.value.istitle()  # Should be title case


@pytest.mark.unit
class TestWeberPennTreeEdgeCases:
    """Test WeberPennTree edge cases and error conditions."""
    
    def test_wpt_without_native_plugin(self):
        """Test WeberPennTree behavior when native plugin is not available."""
        # Check if we're in an environment where WPT functions are available
        from pyhelios.wrappers.UWeberPennTreeWrapper import _WPT_FUNCTIONS_AVAILABLE
        
        if _WPT_FUNCTIONS_AVAILABLE:
            # If WPT functions are available, skip this test as it's designed for mock mode
            pytest.skip("WeberPennTree plugin is available, skipping mock mode test")
        
        mock_context = Mock()
        
        # Test that WeberPennTree creation fails when functions aren't available
        with pytest.raises(NotImplementedError) as exc_info:
            WeberPennTree(mock_context)
        
        assert "WeberPennTree functions not available" in str(exc_info.value)
    
    @pytest.mark.slow
    def test_wpt_memory_cleanup(self, basic_context):
        """Test that WeberPennTree properly cleans up memory."""
        from pyhelios.WeberPennTree import is_weberpenntree_available
        if not is_weberpenntree_available():
            pytest.skip("Requires WeberPennTree plugin for memory testing")
        
        # Create and destroy multiple WeberPennTree instances
        for i in range(5):
            with WeberPennTree(basic_context) as wpt:
                # Generate trees
                for j in range(3):
                    tree_id = wpt.buildTree(WPTType.LEMON, origin=DataTypes.vec3(j, 0, 0))
                    stats = GeometryValidator.validate_tree_structure(wpt, tree_id)
                    assert stats['valid']
            # WeberPennTree should be cleaned up here

# ---------------------------------------------------------------------------
# Tree parameters and random seed
# ---------------------------------------------------------------------------

from pyhelios.WeberPennTree import WeberPennTreeParameters
from pyhelios.exceptions import HeliosRuntimeError


def _valid_parameters(levels=2):
    n = levels + 1
    return WeberPennTreeParameters(
        label='Test', Shape=0, BaseSize=0.2, Scale=3.0, Ratio=0.02, RatioPower=1.2, Levels=levels,
        nSegSplits=[0.0] * n, nSplitAngle=[0.0] * n, nSplitAngleV=[0.0] * n, nCurveRes=[5] * n,
        nCurve=[0.0] * n, nCurveV=[0.0] * n, nCurveBack=[0.0] * n, nLength=[1.0] * n, nLengthV=[0.0] * n,
        nTaper=[1.0] * n, nDownAngle=[0.0] * n, nDownAngleV=[0.0] * n, nRotate=[0.0] * n, nRotateV=[0.0] * n,
        nBranches=[0] + [5] * levels, LeafFile='leaf.png', Leaves=10, LeafScale=0.1, LeafScaleX=0.5,
    )


def _bare_wpt():
    """WeberPennTree instance with no native object, for exercising argument validation."""
    wpt = object.__new__(WeberPennTree)
    wpt.wpt = None
    wpt.context = None
    return wpt


@pytest.mark.cross_platform
class TestTreeParametersValidation:
    """Pure-Python validation of WeberPennTreeParameters and the parameter/seed methods."""

    def test_valid_parameters_pass(self):
        _valid_parameters().validate()

    def test_dataclass_fields_mirror_cpp_struct(self):
        from dataclasses import fields
        names = {f.name for f in fields(WeberPennTreeParameters)}
        expected = {
            'label', 'Shape', 'BaseSize', 'BaseSizeV', 'BaseSplits', 'BaseSplitsV', 'BaseSplitSize',
            'BaseSplitSizeV', 'Scale', 'ScaleV', 'ZScale', 'ZScaleV', 'Ratio', 'RatioPower', 'Lobes',
            'LobeDepth', 'Flare', 'Levels', 'nSegSplits', 'nSplitAngle', 'nSplitAngleV', 'nCurveRes', 'nCurve',
            'nCurveV', 'nCurveBack', 'nLength', 'nLengthV', 'nTaper', 'nDownAngle', 'nDownAngleV', 'nRotate',
            'nRotateV', 'nBranches', 'LeafFile', 'Leaves', 'LeafShape', 'LeafScale', 'LeafScaleX', 'WoodColor',
            'WoodFile', 'leafAngleCDF',
        }
        assert names == expected

    def test_equality(self):
        a, b = _valid_parameters(), _valid_parameters()
        assert a == b
        b.WoodColor = DataTypes.RGBcolor(0.1, 0.2, 0.3)
        assert a != b
        b = _valid_parameters()
        b.nLength[1] = 0.5
        assert a != b

    @pytest.mark.parametrize("levels", [0, 4, -1])
    def test_levels_out_of_range(self, levels):
        p = _valid_parameters()
        p.Levels = levels
        with pytest.raises(ValueError, match="Levels"):
            p.validate()

    def test_per_level_array_too_short(self):
        p = _valid_parameters(levels=3)
        p.nDownAngle = [0.0, 0.0, 0.0]
        with pytest.raises(ValueError, match="nDownAngle has 3 entries"):
            p.validate()

    @pytest.mark.parametrize("field_name,value", [
        ('Scale', 'big'), ('Scale', float('nan')), ('Scale', True), ('Levels', 2.0), ('BaseSplits', -1),
        ('nCurveRes', [5, 5.5, 5]), ('nLength', [1.0, 'x', 1.0]), ('label', 5), ('LeafFile', None),
        ('WoodColor', DataTypes.vec3(0.1, 0.1, 0.1)), ('WoodColor', [0.1, 0.1, 0.1]), ('leafAngleCDF', 0.5),
    ])
    def test_wrong_field_types(self, field_name, value):
        p = _valid_parameters()
        setattr(p, field_name, value)
        with pytest.raises(ValueError, match=field_name):
            p.validate()

    def test_set_rejects_non_parameters_positional_and_keyword(self):
        wpt = _bare_wpt()
        with pytest.raises(ValueError, match="WeberPennTreeParameters"):
            wpt.setTreeParameters('Lemon', {'Scale': 1.0})
        with pytest.raises(ValueError, match="WeberPennTreeParameters"):
            wpt.setTreeParameters(tree_name='Lemon', parameters=DataTypes.vec3(1, 2, 3))

    def test_set_validates_parameters_before_native_call(self):
        p = _valid_parameters()
        p.Levels = 7
        with pytest.raises(ValueError, match="Levels"):
            _bare_wpt().setTreeParameters('Lemon', p)

    @pytest.mark.parametrize("name", ['', '   ', 5, None, DataTypes.vec3(0, 0, 0)])
    def test_invalid_tree_name(self, name):
        wpt = _bare_wpt()
        with pytest.raises(ValueError, match="tree_name"):
            wpt.getTreeParameters(name)
        with pytest.raises(ValueError, match="tree_name"):
            wpt.setTreeParameters(name, _valid_parameters())

    @pytest.mark.parametrize("seed", [-1, 2**32, 1.5, '3', True, None])
    def test_invalid_seed(self, seed):
        with pytest.raises(ValueError, match="seed"):
            _bare_wpt().seedRandomGenerator(seed)

    def test_wrapper_unavailable_raises(self):
        import pyhelios.wrappers.UWeberPennTreeWrapper as w
        with patch.object(w, '_WPT_PARAMETER_FUNCTIONS_AVAILABLE', False):
            with pytest.raises(NotImplementedError, match="build_helios"):
                w.getTreeParameters(None, 'Lemon')
            with pytest.raises(NotImplementedError, match="build_helios"):
                w.setTreeParameters(None, 'Lemon', {})
            with pytest.raises(NotImplementedError, match="build_helios"):
                w.seedRandomGenerator(None, 1)


def _tree_vertices(context, wpt, tree_id):
    return [tuple(round(c, 7) for v in context.getPrimitiveVertices(u) for c in v.to_list())
            for u in wpt.getAllUUIDs(tree_id)]


def _max_height(context, wpt, uuids):
    return max(v.z for u in uuids for v in context.getPrimitiveVertices(u))


@pytest.mark.native_only
class TestTreeParametersNative:
    """Round-trip, modification and seeding against the native library."""

    @pytest.mark.parametrize("tree_type", list(WPTType) if WPTType is not None else [])
    def test_round_trip_builtin_species(self, weber_penn_tree, tree_type):
        params = weber_penn_tree.getTreeParameters(tree_type)
        assert isinstance(params, WeberPennTreeParameters)
        assert params.label == tree_type.value
        assert len(params.nLength) >= params.Levels + 1
        weber_penn_tree.setTreeParameters(tree_type, params)
        again = weber_penn_tree.getTreeParameters(tree_type.value)
        assert again == params

    def test_get_unknown_tree_raises(self, weber_penn_tree):
        with pytest.raises(HeliosRuntimeError, match="does not exist"):
            weber_penn_tree.getTreeParameters("NoSuchTree")

    def test_modified_scale_changes_geometry(self, weber_penn_tree, basic_context):
        weber_penn_tree.seedRandomGenerator(42)
        base_id = weber_penn_tree.buildTree(WPTType.LEMON)
        base_height = _max_height(basic_context, weber_penn_tree, weber_penn_tree.getTrunkUUIDs(base_id))

        params = weber_penn_tree.getTreeParameters(WPTType.LEMON)
        params.Scale = params.Scale * 2.0
        weber_penn_tree.setTreeParameters(WPTType.LEMON, params)
        assert weber_penn_tree.getTreeParameters(WPTType.LEMON).Scale == params.Scale

        weber_penn_tree.seedRandomGenerator(42)
        big_id = weber_penn_tree.buildTree(WPTType.LEMON)
        big_height = _max_height(basic_context, weber_penn_tree, weber_penn_tree.getTrunkUUIDs(big_id))
        assert big_height > 1.5 * base_height

    def test_modified_levels_changes_geometry(self, weber_penn_tree):
        params = weber_penn_tree.getTreeParameters(WPTType.LEMON)
        assert params.Levels >= 2
        weber_penn_tree.seedRandomGenerator(7)
        full_id = weber_penn_tree.buildTree(WPTType.LEMON)
        params.Levels = 1
        weber_penn_tree.setTreeParameters(WPTType.LEMON, params)
        weber_penn_tree.seedRandomGenerator(7)
        reduced_id = weber_penn_tree.buildTree(WPTType.LEMON)
        assert len(weber_penn_tree.getBranchUUIDs(reduced_id)) < len(weber_penn_tree.getBranchUUIDs(full_id))

    def test_define_new_species(self, weber_penn_tree, basic_context):
        params = weber_penn_tree.getTreeParameters(WPTType.LEMON)
        params.label = 'TallLemon'
        params.Scale = params.Scale * 3.0
        weber_penn_tree.setTreeParameters('TallLemon', params)
        assert weber_penn_tree.getTreeParameters('TallLemon') == params
        # The original species is untouched
        assert weber_penn_tree.getTreeParameters(WPTType.LEMON).Scale * 3.0 == pytest.approx(params.Scale)

        weber_penn_tree.seedRandomGenerator(3)
        lemon_id = weber_penn_tree.buildTree(WPTType.LEMON)
        weber_penn_tree.seedRandomGenerator(3)
        tall_id = weber_penn_tree.buildTree('TallLemon')
        assert len(weber_penn_tree.getLeafUUIDs(tall_id)) > 0
        assert (_max_height(basic_context, weber_penn_tree, weber_penn_tree.getTrunkUUIDs(tall_id))
                > 2.0 * _max_height(basic_context, weber_penn_tree, weber_penn_tree.getTrunkUUIDs(lemon_id)))

    def test_new_species_name_with_xml_special_characters(self, weber_penn_tree):
        params = weber_penn_tree.getTreeParameters(WPTType.OLIVE)
        name = 'Olive <"A&B\'s">'
        weber_penn_tree.setTreeParameters(name, params)
        assert weber_penn_tree.getTreeParameters(name) == params

    def test_invalid_native_parameters_rejected_without_side_effects(self, weber_penn_tree):
        params = weber_penn_tree.getTreeParameters(WPTType.LEMON)
        bad = weber_penn_tree.getTreeParameters(WPTType.LEMON)
        bad.Scale = -1.0
        with pytest.raises(HeliosRuntimeError, match="Scale"):
            weber_penn_tree.setTreeParameters(WPTType.LEMON, bad)
        assert weber_penn_tree.getTreeParameters(WPTType.LEMON) == params
        with pytest.raises(HeliosRuntimeError, match="Scale"):
            weber_penn_tree.setTreeParameters('BrandNewBad', bad)
        with pytest.raises(HeliosRuntimeError, match="does not exist"):
            weber_penn_tree.getTreeParameters('BrandNewBad')

    def test_same_seed_reproduces_geometry(self, weber_penn_tree, basic_context):
        weber_penn_tree.seedRandomGenerator(12345)
        first = weber_penn_tree.buildTree(WPTType.APPLE)
        weber_penn_tree.seedRandomGenerator(12345)
        second = weber_penn_tree.buildTree(WPTType.APPLE)
        v1 = _tree_vertices(basic_context, weber_penn_tree, first)
        v2 = _tree_vertices(basic_context, weber_penn_tree, second)
        assert len(v1) > 0
        assert v1 == v2

    def test_different_seed_changes_geometry(self, weber_penn_tree, basic_context):
        weber_penn_tree.seedRandomGenerator(1)
        first = weber_penn_tree.buildTree(WPTType.APPLE)
        weber_penn_tree.seedRandomGenerator(2)
        second = weber_penn_tree.buildTree(WPTType.APPLE)
        assert (_tree_vertices(basic_context, weber_penn_tree, first)
                != _tree_vertices(basic_context, weber_penn_tree, second))
