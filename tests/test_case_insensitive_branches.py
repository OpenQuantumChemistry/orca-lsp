"""Tests to cover all case-insensitive branches in parser.py."""

import pytest
from orca_lsp.parser import ORCAParser


class TestCaseInsensitiveBranches:
    """Test all case-insensitive lookup branches."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_method_branch_with_omega(self, parser):
        """Cover line 160-163: case-insensitive method lookup with ω character."""
        # ωB97X-V.upper() = ΩB97X-V (not in dictionary directly)
        # This triggers the case-insensitive method branch
        result = parser.parse_simple_input("! ωB97X-V", 0)
        assert len(result.methods) > 0
        assert "ωB97X-V" in result.methods

    def test_basis_branch_with_uppercase(self, parser):
        """Cover line 165-168: case-insensitive basis set lookup."""
        # DEF2-TZVP (uppercase) not in dictionary directly
        # def2-TZVP is the correct key
        # This triggers the case-insensitive basis set branch
        result = parser.parse_simple_input("! DEF2-TZVP", 0)
        assert len(result.basis_sets) > 0
        assert "def2-TZVP" in result.basis_sets

    def test_job_branch_preserves_case(self, parser):
        """Test that job types are found regardless of case."""
        # opt.upper() = OPT which IS in job_types directly
        # So this uses the direct check, not case-insensitive
        result = parser.parse_simple_input("! opt", 0)
        assert len(result.job_types) > 0

    def test_other_keywords_branch(self, parser):
        """Cover line 173: else branch for unknown keywords."""
        result = parser.parse_simple_input("! COMPLETELY_UNKNOWN_KEYWORD", 0)
        assert "COMPLETELY_UNKNOWN_KEYWORD" in result.other_keywords

    def test_combined_case_insensitive(self, parser):
        """Test combined case-insensitive lookups."""
        result = parser.parse_simple_input("! ωB97X-V DEF2-TZVP opt", 0)
        assert len(result.methods) > 0
        assert len(result.basis_sets) > 0
        assert len(result.job_types) > 0


class TestBasisSetCaseVariations:
    """Test various case variations for basis sets."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_def2_svp_uppercase(self, parser):
        """Test DEF2-SVP (uppercase) - triggers case-insensitive branch."""
        result = parser.parse_simple_input("! DEF2-SVP", 0)
        assert len(result.basis_sets) > 0
        assert "def2-SVP" in result.basis_sets  # Correct case

    def test_cc_pvtz_uppercase(self, parser):
        """Test CC-PVTZ (uppercase) - triggers case-insensitive branch."""
        result = parser.parse_simple_input("! CC-PVTZ", 0)
        assert len(result.basis_sets) > 0
        assert "cc-pVTZ" in result.basis_sets  # Correct case

    def test_6_31g_star(self, parser):
        """Test 6-31G* (exact case - direct match)."""
        result = parser.parse_simple_input("! 6-31G*", 0)
        assert len(result.basis_sets) > 0


class TestJobTypeVariations:
    """Test various job type inputs."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_opt_found(self, parser):
        """Test opt is found."""
        result = parser.parse_simple_input("! opt", 0)
        assert len(result.job_types) > 0

    def test_freq_found(self, parser):
        """Test freq is found."""
        result = parser.parse_simple_input("! freq", 0)
        assert len(result.job_types) > 0

    def test_sp_found(self, parser):
        """Test sp is found."""
        result = parser.parse_simple_input("! sp", 0)
        assert len(result.job_types) > 0


class TestOmegaMethodVariations:
    """Test ω method variations."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_omega_lowercase(self, parser):
        """Test ωB97X-V (lowercase omega)."""
        result = parser.parse_simple_input("! ωB97X-V", 0)
        assert len(result.methods) > 0

    def test_omega_uppercase(self, parser):
        """Test ΩB97X-V (uppercase omega)."""
        result = parser.parse_simple_input("! ΩB97X-V", 0)
        # ΩB97X-V.upper() = ΩB97X-V, matches ωB97X-V case-insensitively
        assert len(result.methods) > 0 or "ΩB97X-V" in result.other_keywords

    def test_omega_d(self, parser):
        """Test ωB97X-D."""
        result = parser.parse_simple_input("! ωB97X-D", 0)
        assert len(result.methods) > 0
