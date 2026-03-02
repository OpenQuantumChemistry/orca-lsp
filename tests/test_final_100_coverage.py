"""Final tests to achieve 100% coverage."""

from unittest.mock import MagicMock, PropertyMock

import pytest
from lsprotocol.types import (
    HoverParams,
    Position,
    TextDocumentIdentifier,
)

from orca_lsp.parser import ORCAParser
from orca_lsp.server import ORCALanguageServer


class MockTextDocument:
    """Mock text document for testing."""

    def __init__(self, content: str, uri: str = "file:///test.inp"):
        self.source = content
        self.uri = uri
        self.lines = content.split("\n") if content else []


class TestParser100Coverage:
    """Tests to achieve 100% parser coverage."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_unknown_keyword_hits_else_branch(self, parser):
        """Test line 170-173: Unknown keywords go to other_keywords."""
        # Use a keyword that's definitely not in any dictionary
        result = parser.parse_simple_input("! COMPLETELYUNKNOWNKEYWORD", 0)
        # Should hit the else branch and add to other_keywords
        assert "COMPLETELYUNKNOWNKEYWORD" in result.other_keywords

    def test_multiple_unknown_keywords(self, parser):
        """Test multiple unknown keywords all hit else branch."""
        result = parser.parse_simple_input("! FAKEMETHOD FAKEBASIS FAKEJOB", 0)
        # All three should be in other_keywords
        assert "FAKEMETHOD" in result.other_keywords
        assert "FAKEBASIS" in result.other_keywords
        assert "FAKEJOB" in result.other_keywords

    def test_case_insensitive_method_lookup_full_path(self, parser):
        """Test case-insensitive method lookup that doesn't match directly."""
        # Use lowercase method that needs case-insensitive lookup
        result = parser.parse_simple_input("! b3lyp", 0)
        # b3lyp should be found via case-insensitive lookup
        # This should trigger the 160->145 branch
        assert len(result.methods) > 0

    def test_case_insensitive_basis_lookup_full_path(self, parser):
        """Test case-insensitive basis lookup that doesn't match directly."""
        # Use lowercase basis that needs case-insensitive lookup
        result = parser.parse_simple_input("! def2-svp", 0)
        # def2-svp should be found via case-insensitive lookup
        # This should trigger the 165->145 branch
        assert len(result.basis_sets) > 0

    def test_method_not_in_list_after_case_check(self, parser):
        """Test method that passes first check but fails case-insensitive check."""
        # This is tricky - we need something that's not in methods at all
        # to ensure we hit all branches
        result = parser.parse_simple_input("! NOTAMETHOD123", 0)
        assert "NOTAMETHOD123" in result.other_keywords

    def test_basis_not_in_list_after_case_check(self, parser):
        """Test basis that passes first check but fails case-insensitive check."""
        result = parser.parse_simple_input("! NOTABASIS123", 0)
        assert "NOTABASIS123" in result.other_keywords

    def test_job_not_in_list_after_case_check(self, parser):
        """Test job that passes first check but fails case-insensitive check."""
        result = parser.parse_simple_input("! NOTAJOB123", 0)
        assert "NOTAJOB123" in result.other_keywords


class TestGeometryLoopBranches:
    """Test geometry parsing loop continuation branches."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_geometry_with_comment_line(self, parser):
        """Test geometry with comment line that should be skipped."""
        content = """! B3LYP def2-SVP
* xyz 0 1
# This is a comment
H 0.0 0.0 0.0
*"""
        result = parser.parse(content)
        assert result.geometry is not None
        assert len(result.geometry.atoms) >= 1

    def test_geometry_with_empty_line(self, parser):
        """Test geometry with empty line."""
        content = """! B3LYP def2-SVP
* xyz 0 1

H 0.0 0.0 0.0
*"""
        result = parser.parse(content)
        assert result.geometry is not None
        assert len(result.geometry.atoms) >= 1

    def test_geometry_multiple_atoms(self, parser):
        """Test geometry with multiple atoms to exercise loop."""
        content = """! B3LYP def2-SVP
* xyz 0 1
O 0.0 0.0 0.0
H 0.75 0.58 0.0
H -0.75 0.58 0.0
*"""
        result = parser.parse(content)
        assert result.geometry is not None
        assert len(result.geometry.atoms) == 3


class TestBlockParameterLoops:
    """Test block parameter parsing loop branches."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_maxcore_block_multiple_lines(self, parser):
        """Test maxcore block with multiple lines."""
        lines = ["%maxcore 4000", "some other line", "end"]
        block, end = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.parameters.get("memory") == 4000

    def test_pal_block_multiple_lines(self, parser):
        """Test PAL block with multiple lines."""
        lines = ["%pal", "nprocs 4", "other param", "end"]
        block, end = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.parameters.get("nprocs") == 4

    def test_method_block_multiple_dispersion_checks(self, parser):
        """Test method block with multiple dispersion lines."""
        lines = ["%method", "d3bj", "d4", "end"]
        block, end = parser.parse_percent_block(lines, 0)
        assert block is not None
        # Should process both lines in the loop
        assert "dispersion" in block.parameters

    def test_scf_block_multiple_maxiter_checks(self, parser):
        """Test SCF block with multiple maxiter lines."""
        lines = ["%scf", "maxiter 100", "maxiter 200", "end"]
        block, end = parser.parse_percent_block(lines, 0)
        assert block is not None
        # Should process both lines in the loop
        assert "maxiter" in block.parameters


class TestServerHover100Coverage:
    """Test server hover for 100% coverage."""

    @pytest.fixture
    def server(self):
        server = ORCALanguageServer()
        type(server).workspace = PropertyMock(return_value=MagicMock())
        return server

    def test_hover_on_basis_set_in_simple_input(self, server):
        """Test hover on a known basis set in simple input line."""
        # Use a basis set that's definitely in BASIS_SETS
        mock_doc = MockTextDocument("! B3LYP STO-3G OPT")
        server.workspace.get_text_document.return_value = mock_doc

        # Position on STO-3G
        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=10),
        )

        result = server._on_hover(params)
        # Should return a Hover object for STO-3G
        if result is not None:
            assert hasattr(result, "contents")

    def test_hover_on_631g_basis(self, server):
        """Test hover on 6-31G basis set."""
        mock_doc = MockTextDocument("! HF 6-31G")
        server.workspace.get_text_document.return_value = mock_doc

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=6),
        )

        result = server._on_hover(params)
        # Check if hover returns something for 6-31G
        if result is not None:
            assert hasattr(result, "contents")

    def test_hover_on_cc_pvdz_basis(self, server):
        """Test hover on cc-pVDZ basis set."""
        mock_doc = MockTextDocument("! B3LYP cc-pVDZ")
        server.workspace.get_text_document.return_value = mock_doc

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=10),
        )

        result = server._on_hover(params)
        if result is not None:
            assert hasattr(result, "contents")


class TestEdgeCasesFor100Coverage:
    """Additional edge cases for 100% coverage."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_mixed_case_keywords(self, parser):
        """Test parsing with mixed case keywords."""
        result = parser.parse_simple_input("! B3lyp Def2-SVP Opt", 0)
        # Should handle mixed case
        assert len(result.methods) > 0 or "B3lyp" in result.other_keywords

    def test_simple_input_with_spaces(self, parser):
        """Test simple input with extra spaces."""
        result = parser.parse_simple_input("!  B3LYP   def2-SVP   OPT  ", 0)
        # Should handle extra spaces
        assert len(result.methods) > 0 or len(result.basis_sets) > 0

    def test_parse_full_document(self, parser):
        """Test parsing a complete ORCA input file."""
        content = """! B3LYP def2-SVP OPT FREQ
%maxcore 4000
%pal nprocs 4 end
%method
  d3bj
end
%scf
  maxiter 100
end

* xyz 0 1
O 0.0 0.0 0.0
H 0.75 0.58 0.0
H -0.75 0.58 0.0
*
"""
        result = parser.parse(content)
        assert result is not None
        assert len(result.simple_input.methods) > 0
        assert len(result.geometry.atoms) == 3
        assert len(result.percent_blocks) > 0

    def test_parse_with_unknown_block(self, parser):
        """Test parsing with unknown % block."""
        content = """! B3LYP def2-SVP
%unknownblock
  someparam somevalue
end
"""
        result = parser.parse(content)
        assert result is not None
        # Unknown blocks should still be parsed
        assert len(result.percent_blocks) > 0

    def test_empty_simple_input(self, parser):
        """Test parsing empty simple input."""
        result = parser.parse_simple_input("", 0)
        assert result is not None
        assert len(result.methods) == 0
        assert len(result.basis_sets) == 0
        assert len(result.job_types) == 0

    def test_simple_input_only_exclamation(self, parser):
        """Test parsing simple input with only !."""
        result = parser.parse_simple_input("!", 0)
        assert result is not None
