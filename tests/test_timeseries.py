"""
Tests for Context timeseries functionality.

Tests cover the timeseries methods: addTimeseriesData, queryTimeseriesData,
loadTabularTimeseriesData, and related utility methods.
"""

import os
import tempfile

import pytest

from pyhelios import Context
from pyhelios.wrappers.DataTypes import Date, Time
from tests.conftest import is_native_library_available


# ============================================================================
# Input Validation Tests (work in mock mode)
# ============================================================================

@pytest.mark.unit
@pytest.mark.cross_platform
class TestTimeseriesValidation:
    """Test input validation for timeseries methods."""

    def test_add_timeseries_data_invalid_label(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="non-empty string"):
                ctx.addTimeseriesData("", 1.0, Date(2024, 1, 1), Time(12, 0, 0))

    def test_add_timeseries_data_invalid_date_type(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="Date instance"):
                ctx.addTimeseriesData("temp", 1.0, "2024-01-01", Time(12, 0, 0))

    def test_add_timeseries_data_invalid_time_type(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="Time instance"):
                ctx.addTimeseriesData("temp", 1.0, Date(2024, 1, 1), "12:00:00")

    def test_set_current_timeseries_point_invalid_label(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="non-empty string"):
                ctx.setCurrentTimeseriesPoint("", 0)

    def test_update_timeseries_data_invalid_label(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="non-empty string"):
                ctx.updateTimeseriesData("", Date(2024, 1, 1), Time(12, 0, 0), 1.0)

    def test_update_timeseries_data_invalid_date_type(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="Date instance"):
                ctx.updateTimeseriesData("temp", "2024-01-01", Time(12, 0, 0), 1.0)

    def test_update_timeseries_data_invalid_time_type(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="Time instance"):
                ctx.updateTimeseriesData("temp", Date(2024, 1, 1), "12:00:00", 1.0)

    def test_set_current_timeseries_point_negative_index(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="non-negative integer"):
                ctx.setCurrentTimeseriesPoint("temp", -1)

    def test_query_timeseries_data_both_datetime_and_index(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="Cannot specify both"):
                ctx.queryTimeseriesData("temp", date=Date(2024, 1, 1), time=Time(12, 0, 0), index=0)

    def test_query_timeseries_data_date_without_time(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="Both date and time"):
                ctx.queryTimeseriesData("temp", date=Date(2024, 1, 1))

    def test_query_timeseries_data_time_without_date(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="Both date and time"):
                ctx.queryTimeseriesData("temp", time=Time(12, 0, 0))

    def test_query_timeseries_data_invalid_date_type(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="Date instance"):
                ctx.queryTimeseriesData("temp", date="2024-01-01", time=Time(12, 0, 0))

    def test_query_timeseries_data_invalid_time_type(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="Time instance"):
                ctx.queryTimeseriesData("temp", date=Date(2024, 1, 1), time="12:00")

    def test_query_timeseries_data_negative_index(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="non-negative integer"):
                ctx.queryTimeseriesData("temp", index=-1)

    def test_query_timeseries_time_invalid_label(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="non-empty string"):
                ctx.queryTimeseriesTime("", 0)

    def test_query_timeseries_date_negative_index(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="non-negative integer"):
                ctx.queryTimeseriesDate("temp", -1)

    def test_get_timeseries_length_invalid_label(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="non-empty string"):
                ctx.getTimeseriesLength("")

    def test_does_timeseries_variable_exist_invalid_label(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="non-empty string"):
                ctx.doesTimeseriesVariableExist("")

    def test_load_tabular_empty_file_path(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="non-empty string"):
                ctx.loadTabularTimeseriesData("", ["date", "temp"])

    def test_load_tabular_empty_column_labels(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="non-empty list"):
                ctx.loadTabularTimeseriesData("data.csv", [])

    def test_load_tabular_invalid_column_label_type(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="must be a string"):
                ctx.loadTabularTimeseriesData("data.csv", ["date", 123])

    def test_load_tabular_empty_delimiter(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="non-empty string"):
                ctx.loadTabularTimeseriesData("data.csv", ["date", "temp"], delimiter="")

    def test_delete_timeseries_data_point_invalid_date_type(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="date must be a Date"):
                ctx.deleteTimeseriesDataPoint("notadate", Time(0, 0, 0), "temp")

    def test_delete_timeseries_data_point_invalid_time_type(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="time must be a Time"):
                ctx.deleteTimeseriesDataPoint(Date(2024, 1, 1), "notatime", "temp")

    def test_delete_timeseries_data_point_invalid_label(self):
        with Context() as ctx:
            with pytest.raises(ValueError, match="non-empty string or None"):
                ctx.deleteTimeseriesDataPoint(Date(2024, 1, 1), Time(0, 0, 0), "")


# ============================================================================
# Native Library Tests (require compiled Helios)
# ============================================================================

@pytest.mark.native_only
@pytest.mark.integration
class TestTimeseriesNative:
    """Test timeseries functionality with native Helios library."""

    @pytest.fixture(autouse=True)
    def skip_if_no_native(self):
        if not is_native_library_available():
            pytest.skip("Native Helios library not available")

    def test_add_and_query_single_point(self):
        with Context() as ctx:
            ctx.addTimeseriesData("temperature", 25.3, Date(2024, 6, 15), Time(12, 0, 0))
            val = ctx.queryTimeseriesData("temperature", index=0)
            assert val == pytest.approx(25.3, abs=1e-4)

    def test_add_multiple_points_query_by_index(self):
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(6, 0, 0))
            ctx.addTimeseriesData("temp", 25.0, Date(2024, 1, 1), Time(12, 0, 0))
            ctx.addTimeseriesData("temp", 22.0, Date(2024, 1, 1), Time(18, 0, 0))

            assert ctx.queryTimeseriesData("temp", index=0) == pytest.approx(20.0, abs=1e-4)
            assert ctx.queryTimeseriesData("temp", index=1) == pytest.approx(25.0, abs=1e-4)
            assert ctx.queryTimeseriesData("temp", index=2) == pytest.approx(22.0, abs=1e-4)

    def test_update_existing_point(self):
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 25.3, Date(2024, 6, 15), Time(12, 0, 0))
            assert ctx.queryTimeseriesData("temp", index=0) == pytest.approx(25.3, abs=1e-4)

            ctx.updateTimeseriesData("temp", Date(2024, 6, 15), Time(12, 0, 0), 30.0)
            assert ctx.queryTimeseriesData("temp", index=0) == pytest.approx(30.0, abs=1e-4)

    def test_update_unknown_variable_raises(self):
        from pyhelios.exceptions import HeliosError
        with Context() as ctx:
            with pytest.raises(HeliosError):
                ctx.updateTimeseriesData("nonexistent", Date(2024, 1, 1), Time(0, 0, 0), 1.0)

    def test_update_unknown_timestamp_raises(self):
        from pyhelios.exceptions import HeliosError
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(6, 0, 0))
            with pytest.raises(HeliosError):
                ctx.updateTimeseriesData("temp", Date(2024, 1, 1), Time(7, 0, 0), 99.0)

    def test_query_with_interpolation(self):
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(6, 0, 0))
            ctx.addTimeseriesData("temp", 30.0, Date(2024, 1, 1), Time(12, 0, 0))

            # Query at midpoint should interpolate to ~25.0
            val = ctx.queryTimeseriesData("temp", date=Date(2024, 1, 1), time=Time(9, 0, 0))
            assert val == pytest.approx(25.0, abs=1.0)

    def test_query_at_current_context_time(self):
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(hour=6, minute=0, second=0))
            ctx.addTimeseriesData("temp", 30.0, Date(2024, 1, 1), Time(hour=12, minute=0, second=0))

            # Use setCurrentTimeseriesPoint to set context to first data point
            ctx.setCurrentTimeseriesPoint("temp", 0)
            val = ctx.queryTimeseriesData("temp")
            assert val == pytest.approx(20.0, abs=1e-4)

    def test_set_current_timeseries_point(self):
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 3, 15), Time(hour=8, minute=0, second=0))
            ctx.addTimeseriesData("temp", 25.0, Date(2024, 6, 15), Time(hour=14, minute=0, second=0))

            # After setting to index 1, querying at current time should return second value
            ctx.setCurrentTimeseriesPoint("temp", 1)
            val = ctx.queryTimeseriesData("temp")
            assert val == pytest.approx(25.0, abs=1e-4)

    def test_get_timeseries_length(self):
        with Context() as ctx:
            assert ctx.doesTimeseriesVariableExist("nonexistent") is False

            ctx.addTimeseriesData("humidity", 0.5, Date(2024, 1, 1), Time(0, 0, 0))
            ctx.addTimeseriesData("humidity", 0.6, Date(2024, 1, 1), Time(6, 0, 0))
            ctx.addTimeseriesData("humidity", 0.7, Date(2024, 1, 1), Time(12, 0, 0))

            assert ctx.getTimeseriesLength("humidity") == 3

    def test_does_timeseries_variable_exist(self):
        with Context() as ctx:
            assert ctx.doesTimeseriesVariableExist("nonexistent") is False

            ctx.addTimeseriesData("pressure", 101325.0, Date(2024, 1, 1), Time(0, 0, 0))
            assert ctx.doesTimeseriesVariableExist("pressure") is True
            assert ctx.doesTimeseriesVariableExist("other") is False

    def test_list_timeseries_variables(self):
        with Context() as ctx:
            assert ctx.listTimeseriesVariables() == []

            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(0, 0, 0))
            ctx.addTimeseriesData("humidity", 0.5, Date(2024, 1, 1), Time(0, 0, 0))

            variables = ctx.listTimeseriesVariables()
            assert "temp" in variables
            assert "humidity" in variables
            assert len(variables) == 2

    def test_query_timeseries_time(self):
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(14, 30, 15))

            t = ctx.queryTimeseriesTime("temp", 0)
            assert isinstance(t, Time)
            assert t.hour == 14
            assert t.minute == 30
            assert t.second == 15

    def test_query_timeseries_date(self):
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 7, 4), Time(12, 0, 0))

            d = ctx.queryTimeseriesDate("temp", 0)
            assert isinstance(d, Date)
            assert d.year == 2024
            assert d.month == 7
            assert d.day == 4

    def test_load_tabular_timeseries_data(self):
        # Create a temp CSV file
        csv_content = "20240101,6,20.5,0.65\n20240101,12,28.3,0.45\n20240101,18,24.1,0.55\n"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            with Context() as ctx:
                ctx.loadTabularTimeseriesData(
                    temp_path,
                    column_labels=["date", "hour", "temperature", "humidity"],
                    delimiter=","
                )

                assert ctx.doesTimeseriesVariableExist("temperature") is True
                assert ctx.doesTimeseriesVariableExist("humidity") is True
                assert ctx.getTimeseriesLength("temperature") == 3

                val = ctx.queryTimeseriesData("temperature", index=0)
                assert val == pytest.approx(20.5, abs=0.1)
        finally:
            os.unlink(temp_path)

    def test_multiple_variables_independent(self):
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(6, 0, 0))
            ctx.addTimeseriesData("temp", 25.0, Date(2024, 1, 1), Time(12, 0, 0))
            ctx.addTimeseriesData("wind", 3.5, Date(2024, 1, 1), Time(6, 0, 0))
            ctx.addTimeseriesData("wind", 5.2, Date(2024, 1, 1), Time(12, 0, 0))

            assert ctx.getTimeseriesLength("temp") == 2
            assert ctx.getTimeseriesLength("wind") == 2
            assert ctx.queryTimeseriesData("temp", index=0) == pytest.approx(20.0, abs=1e-4)
            assert ctx.queryTimeseriesData("wind", index=0) == pytest.approx(3.5, abs=1e-4)

    def test_clear_timeseries_data(self):
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(6, 0, 0))
            ctx.addTimeseriesData("temp", 25.0, Date(2024, 1, 1), Time(12, 0, 0))
            ctx.addTimeseriesData("wind", 3.5, Date(2024, 1, 1), Time(6, 0, 0))

            ctx.clearTimeseriesData()

            assert ctx.listTimeseriesVariables() == []
            assert ctx.doesTimeseriesVariableExist("temp") is False
            assert ctx.doesTimeseriesVariableExist("wind") is False

    def test_clear_then_readd(self):
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(6, 0, 0))
            ctx.clearTimeseriesData()

            ctx.addTimeseriesData("humidity", 65.0, Date(2024, 1, 1), Time(12, 0, 0))

            assert ctx.listTimeseriesVariables() == ["humidity"]
            assert ctx.doesTimeseriesVariableExist("temp") is False
            assert ctx.queryTimeseriesData("humidity", index=0) == pytest.approx(65.0, abs=1e-4)

    def test_clear_empty_context(self):
        with Context() as ctx:
            ctx.clearTimeseriesData()
            assert ctx.listTimeseriesVariables() == []

    def test_delete_timeseries_variable(self):
        """`deleteTimeseriesVariable` should remove only the named series."""
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(6, 0, 0))
            ctx.addTimeseriesData("temp", 25.0, Date(2024, 1, 1), Time(12, 0, 0))
            ctx.addTimeseriesData("wind", 3.5, Date(2024, 1, 1), Time(6, 0, 0))

            ctx.deleteTimeseriesVariable("temp")

            assert ctx.doesTimeseriesVariableExist("temp") is False
            assert ctx.doesTimeseriesVariableExist("wind") is True
            # Other series should be untouched.
            assert ctx.getTimeseriesLength("wind") == 1

    def test_delete_timeseries_variable_missing_is_noop(self):
        """Deleting a non-existent variable issues a warning but does not raise."""
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(6, 0, 0))
            # Underlying Helios issues a non-fatal warning to stderr — should not raise.
            ctx.deleteTimeseriesVariable("nonexistent")
            assert ctx.doesTimeseriesVariableExist("temp") is True

    def test_delete_timeseries_variable_empty_label_raises(self):
        with Context() as ctx:
            with pytest.raises(ValueError):
                ctx.deleteTimeseriesVariable("")

    def test_delete_timeseries_data_point_single_variable(self):
        """`deleteTimeseriesDataPoint` with a label removes only that point of that variable."""
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(6, 0, 0))
            ctx.addTimeseriesData("temp", 25.0, Date(2024, 1, 1), Time(12, 0, 0))
            assert ctx.getTimeseriesLength("temp") == 2

            ctx.deleteTimeseriesDataPoint(Date(2024, 1, 1), Time(6, 0, 0), "temp")

            assert ctx.getTimeseriesLength("temp") == 1
            # The surviving point is the 12:00 value.
            assert ctx.queryTimeseriesData("temp", index=0) == pytest.approx(25.0, abs=1e-4)

    def test_delete_timeseries_data_point_all_variables(self):
        """`deleteTimeseriesDataPoint` without a label removes the point from every variable."""
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(6, 0, 0))
            ctx.addTimeseriesData("temp", 25.0, Date(2024, 1, 1), Time(12, 0, 0))
            ctx.addTimeseriesData("wind", 3.5, Date(2024, 1, 1), Time(6, 0, 0))

            ctx.deleteTimeseriesDataPoint(Date(2024, 1, 1), Time(6, 0, 0))

            assert ctx.getTimeseriesLength("temp") == 1
            assert ctx.queryTimeseriesData("temp", index=0) == pytest.approx(25.0, abs=1e-4)
            # wind only had the 6:00 point, so it is now empty.
            assert ctx.getTimeseriesLength("wind") == 0

    def test_delete_timeseries_data_point_missing_is_noop(self):
        """Deleting a non-existent point issues a warning but does not raise."""
        with Context() as ctx:
            ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(6, 0, 0))
            ctx.deleteTimeseriesDataPoint(Date(2099, 1, 1), Time(0, 0, 0), "temp")
            assert ctx.getTimeseriesLength("temp") == 1


# ============================================================================
# Mock Mode Tests
# ============================================================================

@pytest.mark.mock_mode
@pytest.mark.cross_platform
class TestTimeseriesMockMode:
    """Test that timeseries methods raise appropriate errors in mock mode."""

    @pytest.fixture(autouse=True)
    def skip_if_native(self):
        if is_native_library_available():
            pytest.skip("Test is for mock mode only - native library is available")

    def test_add_timeseries_data_mock_mode(self):
        with Context() as ctx:
            with pytest.raises((RuntimeError, NotImplementedError)):
                ctx.addTimeseriesData("temp", 20.0, Date(2024, 1, 1), Time(12, 0, 0))

    def test_query_timeseries_data_mock_mode(self):
        with Context() as ctx:
            with pytest.raises((RuntimeError, NotImplementedError)):
                ctx.queryTimeseriesData("temp")

    def test_load_tabular_timeseries_data_mock_mode(self):
        with Context() as ctx:
            with pytest.raises((RuntimeError, NotImplementedError)):
                ctx.loadTabularTimeseriesData("data.csv", ["date", "temp"])

    def test_list_timeseries_variables_mock_mode(self):
        with Context() as ctx:
            with pytest.raises((RuntimeError, NotImplementedError)):
                ctx.listTimeseriesVariables()

    def test_get_timeseries_length_mock_mode(self):
        with Context() as ctx:
            with pytest.raises((RuntimeError, NotImplementedError)):
                ctx.getTimeseriesLength("temp")

    def test_does_timeseries_variable_exist_mock_mode(self):
        with Context() as ctx:
            with pytest.raises((RuntimeError, NotImplementedError)):
                ctx.doesTimeseriesVariableExist("temp")

    def test_clear_timeseries_data_mock_mode(self):
        with Context() as ctx:
            with pytest.raises((RuntimeError, NotImplementedError)):
                ctx.clearTimeseriesData()
