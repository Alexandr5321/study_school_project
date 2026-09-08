from app import create_app


def test_app_creation():
    app = create_app()

    assert app is not None
    assert app.config["SECRET_KEY"]


def test_index_page():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
