from scheduler import app


def test_get_status_200(testing_app):
    """Testing get_status."""
    body = {"unit_id": "uid_1"}
    response = testing_app.get("/unit", params=body)
    assert response.status_code == 200
    assert response.json() == {"status": "Finished"}


def test_get_status_404(testing_app):
    """Testing get_status."""
    body = {"unit_id": "not_existing_id"}
    response = testing_app.get("/unit", params=body)
    assert response.status_code == 404
    assert response.json() == {"detail": app.NO_UNIT}


def test_get_status_403(testing_app):
    """Testing get_status."""
    body = {"unit_id": "uid_2"}
    response = testing_app.get("/unit", params=body)
    assert response.status_code == 403
    assert response.json() == {"detail": app.NO_TENANT}
