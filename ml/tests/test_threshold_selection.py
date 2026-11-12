from ml.benchmark.thresholds import confusion


def test_confusion_metrics() -> None:
    metrics = confusion([True, True, False, False], [True, False, True, False])
    assert metrics == {
        "tp": 1,
        "tn": 1,
        "fp": 1,
        "fn": 1,
        "precision": 0.5,
        "sensitivity": 0.5,
        "specificity": 0.5,
        "f1": 0.5,
    }
