import pytest
import arduino
import responses

# Test parameters
ips = {'192.168.1.1', '192.168.1.2'}


@pytest.fixture
def arduino_client(ip):
    return arduino.Client(ip)


@pytest.mark.parametrize("ip", ips)
def test_init_client(arduino_client, ip):
    assert arduino_client.ip == ip


def test_code():
    arduino_client = arduino.Client('192.168.1.112')
    if arduino_client.get_value('rain') is None:
        print('Failed to read from Guard House API')
    else:
        print(arduino_client.get_value('rain'))
