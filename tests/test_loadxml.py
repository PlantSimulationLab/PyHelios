"""
Tests for WeberPennTree loadXML functionality.

These tests verify the loadXML method for loading custom tree species from XML files.
"""

import pytest
from pyhelios import Context, WeberPennTree, WPTType
from pyhelios.exceptions import HeliosRuntimeError
from tests.test_utils import GeometryValidator


def create_minimal_tree_xml(label: str, leaves: int = 10, branches: int = 10) -> str:
    """Create a minimal valid WeberPennTree XML with all required parameters."""
    return f'''<?xml version="1.0"?>
<helios>
<WeberPennTree label="{label}">
  <Shape>0</Shape>
  <BaseSize>0.4</BaseSize>
  <BaseSplits>0</BaseSplits>
  <BaseSplitSize>0.2</BaseSplitSize>
  <Scale>1.0</Scale>
  <ScaleV>0.0</ScaleV>
  <ZScale>1.0</ZScale>
  <ZScaleV>0.0</ZScaleV>
  <Ratio>0.015</Ratio>
  <RatioPower>1.3</RatioPower>
  <Flare>0.6</Flare>
  <Lobes>0</Lobes>
  <LobeDepth>0</LobeDepth>
  <Levels>2</Levels>
  <nSegSplits>0 0 0</nSegSplits>
  <nSplitAngle>0 0 0</nSplitAngle>
  <nSplitAngleV>0 0 0</nSplitAngleV>
  <nCurveRes>5 5 5</nCurveRes>
  <nCurve>0 -40 -40</nCurve>
  <nCurveV>20 10 10</nCurveV>
  <nCurveBack>0 0 0</nCurveBack>
  <nLength>1 0.6 0.5</nLength>
  <nLengthV>0 0 0</nLengthV>
  <nTaper>1 1 1</nTaper>
  <nDownAngle>0 60 45</nDownAngle>
  <nDownAngleV>0 10 10</nDownAngleV>
  <nRotate>140 140 140</nRotate>
  <nRotateV>0 0 0</nRotateV>
  <nBranches>0 {branches} 0</nBranches>
  <Leaves>{leaves}</Leaves>
  <LeafFile>plugins/weberpenntree/leaves/AlmondLeaf.png</LeafFile>
  <LeafScale>0.1</LeafScale>
  <LeafScaleX>1.0</LeafScaleX>
  <WoodFile>plugins/weberpenntree/wood/wood2.jpg</WoodFile>
</WeberPennTree>
</helios>
'''


@pytest.mark.native_only
class TestCustomTreeLoading:
    """Test loading custom tree species from XML files."""

    def test_loadXML_with_valid_file(self, weber_penn_tree, tmp_path):
        """Test loading custom tree from valid XML file."""
        xml_file = tmp_path / "test_tree.xml"
        xml_file.write_text(create_minimal_tree_xml("TestTree"))

        weber_penn_tree.loadXML(str(xml_file), silent=True)
        tree_id = weber_penn_tree.buildTree("TestTree")

        assert isinstance(tree_id, int)
        assert tree_id >= 0

        stats = GeometryValidator.validate_tree_structure(weber_penn_tree, tree_id)
        assert stats['valid']

    def test_loadXML_with_relative_path(self, weber_penn_tree, tmp_path, monkeypatch):
        """Test loading XML file with relative path."""
        xml_file = tmp_path / "relative_tree.xml"
        xml_file.write_text(create_minimal_tree_xml("RelativePathTree", leaves=5, branches=8))
        monkeypatch.chdir(tmp_path)

        weber_penn_tree.loadXML("relative_tree.xml", silent=True)
        tree_id = weber_penn_tree.buildTree("RelativePathTree")
        assert tree_id >= 0

    def test_loadXML_silent_parameter(self, weber_penn_tree, tmp_path):
        """Test silent parameter suppresses output."""
        xml_file = tmp_path / "silent_tree.xml"
        xml_file.write_text(create_minimal_tree_xml("SilentTree", leaves=5, branches=5))

        weber_penn_tree.loadXML(str(xml_file), silent=False)
        weber_penn_tree.loadXML(str(xml_file), silent=True)

    def test_loadXML_nonexistent_file(self, weber_penn_tree):
        """Test error handling for nonexistent XML file."""
        with pytest.raises(ValueError, match="XML file not found"):
            weber_penn_tree.loadXML("/nonexistent/path/to/tree.xml")

    def test_loadXML_invalid_extension(self, weber_penn_tree, tmp_path):
        """Test error handling for non-XML file."""
        txt_file = tmp_path / "not_xml.txt"
        txt_file.write_text("This is not XML")

        with pytest.raises(ValueError, match="File extension '.txt' not allowed"):
            weber_penn_tree.loadXML(str(txt_file))

    def test_loadXML_malformed_xml(self, weber_penn_tree, tmp_path):
        """Test error handling for malformed XML."""
        xml_file = tmp_path / "malformed.xml"
        xml_file.write_text("This is not valid XML <unclosed>")

        with pytest.raises(HeliosRuntimeError):
            weber_penn_tree.loadXML(str(xml_file), silent=True)

    def test_loadXML_empty_filename(self, weber_penn_tree):
        """Test error handling for empty filename."""
        with pytest.raises(ValueError, match="Parameter cannot be empty"):
            weber_penn_tree.loadXML("")

    def test_loadXML_multiple_files(self, weber_penn_tree, tmp_path):
        """Test loading multiple XML files sequentially."""
        file1 = tmp_path / "oak.xml"
        file2 = tmp_path / "maple.xml"
        file1.write_text(create_minimal_tree_xml("CustomOak", leaves=8, branches=12))
        file2.write_text(create_minimal_tree_xml("CustomMaple", leaves=6, branches=10))

        weber_penn_tree.loadXML(str(file1), silent=True)
        weber_penn_tree.loadXML(str(file2), silent=True)

        oak_id = weber_penn_tree.buildTree("CustomOak")
        maple_id = weber_penn_tree.buildTree("CustomMaple")

        assert oak_id >= 0
        assert maple_id >= 0
        assert oak_id != maple_id


@pytest.mark.unit
class TestLoadXMLValidation:
    """Test validation for loadXML method."""

    def test_validation_requires_xml_extension(self, weber_penn_tree, tmp_path):
        """Test that validation requires .xml extension."""
        wrong_ext = tmp_path / "tree.txt"
        wrong_ext.write_text("<?xml version='1.0'?><helios><WeberPennTree label='Test'><Shape>0</Shape></WeberPennTree></helios>")

        with pytest.raises(ValueError, match="File extension '.txt' not allowed"):
            weber_penn_tree.loadXML(str(wrong_ext))

    def test_validation_checks_file_exists(self, weber_penn_tree):
        """Test that validation checks file existence."""
        with pytest.raises(ValueError, match="XML file not found"):
            weber_penn_tree.loadXML("nonexistent_file.xml")
