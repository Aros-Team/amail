"""Tests for provider singleton behavior and Resend SDK timeout configuration."""

from unittest.mock import MagicMock, patch

from amail.providers import get_provider


class TestProviderSingleton:
    """Verify get_provider returns cached instances, not new ones each call."""

    def setup_method(self) -> None:
        """Clear any cached provider instances between tests."""
        from amail.providers import _provider_instance

        _provider_instance.clear()

    def test_get_provider_returns_same_instance_on_multiple_calls(self) -> None:
        """get_provider() must return the same object on repeated calls."""
        provider1 = get_provider("mock")
        provider2 = get_provider("mock")
        assert provider1 is provider2

    def test_get_provider_explicit_name_returns_same_instance(self) -> None:
        """get_provider('mock') must return the same object on repeated calls."""
        p1 = get_provider("mock")
        p2 = get_provider("mock")
        assert p1 is p2

    @patch("amail.providers.resend.sender.get_settings")
    def test_resend_api_key_set_once_not_repeatedly(
        self, mock_get_settings: MagicMock
    ) -> None:
        """resend.api_key should be set during init, not re-mutated every call."""
        import resend

        mock_get_settings.return_value = MagicMock(resend_api_key="test-key")

        provider1 = get_provider("resend")
        assert resend.api_key == "test-key"

        # Second call should return same provider, not re-init
        provider2 = get_provider("resend")
        assert provider1 is provider2

    def test_resend_sdk_timeout_configured_to_10s(self) -> None:
        """ResendSender must configure the SDK HTTP client timeout to 10s."""
        with patch("amail.providers.resend.sender.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(resend_api_key="test-key")
            get_provider("resend")
            # The Resend SDK stores its HTTP client on the module level
            import resend

            client = resend.default_http_client
            assert hasattr(
                client, "_timeout"
            ), "HTTP client should have _timeout attribute"
            assert client._timeout == 10, f"Expected timeout 10, got {client._timeout}"

    def test_reset_provider_singleton_creates_new_instance(self) -> None:
        """After reset, get_provider must return a fresh instance."""
        from amail.providers import reset_provider

        provider1 = get_provider("mock")
        reset_provider("mock")
        provider2 = get_provider("mock")
        assert provider1 is not provider2
