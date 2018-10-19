from .test_fuzzy_matching import test_fuzzy_matching
from .test_model_predictions import test_model_predictions
from .test_reference_number import test_reference_number
from .test_reference_structuring import test_reference_structuring
from .main import run_tests


__all__ = [
    test_fuzzy_matching,
    test_model_predictions,
    test_reference_number,
    test_reference_structuring,
    run_tests
]


if __name__ == '__main__':
    run_tests()
