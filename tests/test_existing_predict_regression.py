"""
Regression test (spec §23): confirms the pre-existing /predict endpoint and
its request/response shape are unchanged by the mental-health module.

Stubs tensorflow because this sandbox doesn't have the real TF install --
this test verifies MY change didn't break the wiring/route table, not the
pre-existing model's numerical behavior (which is untouched code, out of
scope for a change I didn't make).
"""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _install_tf_stub():
    if "tensorflow" in sys.modules:
        return
    tf_stub = types.ModuleType("tensorflow")

    class _FakeModel:
        def predict(self, *a, **k):
            import numpy as np
            return np.array([[0.5]])

    tf_stub.keras = types.SimpleNamespace(
        models=types.SimpleNamespace(load_model=lambda *a, **k: _FakeModel())
    )
    sys.modules["tensorflow"] = tf_stub


def test_existing_predict_endpoint_still_works():
    _install_tf_stub()
    import importlib
    main = importlib.import_module("app.main")
    from fastapi.testclient import TestClient

    client = TestClient(main.app)

    r = client.post("/predict", json={"Age": 28, "BMI": 24.0})
    assert r.status_code == 200
    body = r.json()
    assert "prediction" in body
    assert "prediction_label" in body


def test_existing_root_endpoint_still_works():
    _install_tf_stub()
    import importlib
    main = importlib.import_module("app.main")
    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "Hello World"}


def test_mental_health_router_is_mounted_alongside_existing_routes():
    _install_tf_stub()
    import importlib
    main = importlib.import_module("app.main")

    paths = []
    for route in main.app.routes:
        if hasattr(route, "path"):
            paths.append(route.path)
        elif hasattr(route, "original_router"):  # fastapi._IncludedRouter (mounted sub-router)
            paths.extend(r.path for r in route.original_router.routes)

    assert "/predict" in paths            # existing, untouched
    assert "/" in paths                    # existing, untouched
    assert "/mental-health/patients" in paths  # new
