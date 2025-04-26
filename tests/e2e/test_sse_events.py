import pytest
import sseclient
import requests

def test_sse_events():
    resp = requests.get('http://localhost:5000/events', stream=True)
    client = sseclient.SSEClient(resp)
    msg = next(client)
    assert msg.data == 'reload'
