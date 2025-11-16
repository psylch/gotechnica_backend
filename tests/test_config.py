from src.config import AppSettings


def test_cors_origin_list_parsing():
    settings = AppSettings(cors_origins="http://a.com, http://b.com ,http://c.com")
    assert settings.cors_origin_list == ["http://a.com", "http://b.com", "http://c.com"]


def test_log_level_normalization():
    settings = AppSettings(log_level="info")
    assert settings.log_level == "INFO"


def test_r2_endpoint_url_building():
    settings = AppSettings(r2_account_id="abcd1234")
    assert settings.r2_endpoint_url == "https://abcd1234.r2.cloudflarestorage.com"
