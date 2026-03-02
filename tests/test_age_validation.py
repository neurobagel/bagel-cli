import pytest
import typer

from bagel.mappings import NB
from bagel.utilities.pheno_utils import transform_age

AGE_FLOAT = NB.pf + ":FromFloat"
AGE_INT = NB.pf + ":FromInt"


def test_transform_age_valid_positive():
    """Test that positive ages are transformed correctly."""
    assert transform_age("25.5", AGE_FLOAT) == 25.5
    assert transform_age("30", AGE_INT) == 30.0


def test_transform_age_negative_raises_error():
    """Test that negative ages trigger an error/exit."""
    with pytest.raises(typer.Exit):
        transform_age("-5.0", AGE_FLOAT)

    with pytest.raises(typer.Exit):
        transform_age("-10", AGE_INT)


def test_transform_age_zero_is_valid():
    """Test that age 0 is valid (e.g. newborns)."""
    assert transform_age("0", AGE_INT) == 0.0
