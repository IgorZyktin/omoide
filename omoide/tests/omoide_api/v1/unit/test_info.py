"""Tests."""
import http


def test_info_version(api_test_client):
    response = api_test_client.get('/v1/info/version')

    assert response.status_code == http.HTTPStatus.OK
    assert 'version' in response.json()
