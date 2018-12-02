import pytest
import arduino
import responses

# Test parameters
urls = {'first_url', 'second_url'}


@pytest.fixture
def arduino_client():
    return arduino.Client('url')


@pytest.mark.parametrize("url", urls)
def test_change_name(arduino_client, url):
    arduino_client.set_url(url)
    assert arduino_client.get_url() == url
