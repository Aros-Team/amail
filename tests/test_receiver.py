

class TestResendReceiver:
    def test_receive_returns_ignored_for_unknown_event(self, mock_resend):
        from app.providers.resend.receiver import ResendReceiver

        receiver = ResendReceiver()
        payload = {"type": "unknown.event", "data": {}}

        result = receiver.receive(payload)

        assert result["status"] == "ignored"
        assert result["reason"] == "event type not supported"
        mock_resend.assert_not_called()

    def test_receive_returns_ignored_for_disallowed_email(self, mock_resend):
        from app.providers.resend.receiver import ResendReceiver

        receiver = ResendReceiver()
        payload = {
            "type": "email.received",
            "data": {
                "from": "unknown@test.com",
                "subject": "Test",
                "html": "<html>Test</html>",
            },
        }

        result = receiver.receive(payload)

        assert result["status"] == "ignored"
        assert result["reason"] == "email not in allowed list"
        mock_resend.assert_not_called()

    def test_receive_forwards_allowed_email(self, mock_resend, settings):
        from app.providers.resend.receiver import ResendReceiver

        receiver = ResendReceiver()
        payload = {
            "type": "email.received",
            "data": {
                "from": f"support@{settings.DOMAIN}",
                "subject": "Test Subject",
                "html": "<html>Test</html>",
            },
        }

        result = receiver.receive(payload)

        assert result["status"] == "forwarded"
        mock_resend.assert_called_once()
