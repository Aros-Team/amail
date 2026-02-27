

class TestResendSender:
    def test_send_returns_email_id(self, mock_resend):
        from app.providers.resend.sender import ResendSender

        sender = ResendSender()
        result = sender.send("to@test.com", "Test Subject", "<html>Test</html>")

        assert result == "test-email-id"
        mock_resend.assert_called_once()

    def test_send_uses_correct_from_email(self, mock_resend, settings):
        from app.providers.resend.sender import ResendSender

        sender = ResendSender()
        sender.send("to@test.com", "Test Subject", "<html>Test</html>")

        call_args = mock_resend.call_args[1]
        assert call_args["from"] == f"noreply@{settings.DOMAIN}"
        assert call_args["to"] == ["to@test.com"]
        assert call_args["subject"] == "Test Subject"
