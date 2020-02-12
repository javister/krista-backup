import pytest

@pytest.mark.web
class TestWeb(object):
    def test_web_webapi(self, container):
        container1 = container()
        container2 = container()

        ips = [cont.attrs['NetworkSettings']['IPAddress'] 
            for cont in (container1, container2)
        ]
        assert True
