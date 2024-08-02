import pytest

from app.main import validate_webhook_url

# NB: these takes need internet connectivity!


@pytest.mark.asyncio
async def test_validate_webhook_url_bad():
    url = "https://foo.bar.baz.blam.sjdhgaeriuhfewef.co/foo/bar.baz"
    good = await validate_webhook_url(url)
    assert good is False


@pytest.mark.asyncio
async def test_validate_webhook_url_good():
    url = "https://google.com"
    good = await validate_webhook_url(url)
    assert good


@pytest.mark.asyncio
async def test_validate_webhook_url_bad_protocol():
    url = "foo://google.com"
    good = await validate_webhook_url(url)
    assert good is False
