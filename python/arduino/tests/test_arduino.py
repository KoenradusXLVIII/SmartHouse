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


# def test_code():
#     arduino_client = arduino.Client('http://192.168.1.112/')
#     if not arduino_client.set_value('light_delay',30000):
#         print('Failed to write to Guard House API')
#     else:
#         print(arduino_client.get_value('light_delay'))
