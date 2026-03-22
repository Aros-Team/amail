from prometheus_client import Counter, Gauge, Histogram

email_send_total = Counter(
    "email_send_total",
    "Total number of email send attempts",
    ["status"],
)

email_send_duration_seconds = Histogram(
    "email_send_duration_seconds",
    "Duration of email send calls to Resend",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0],
)

email_retry_total = Counter(
    "email_retry_total",
    "Total number of email retry attempts",
    ["attempt_number"],
)

resend_rate_limit_remaining = Gauge(
    "resend_rate_limit_remaining",
    "Remaining rate limit from Resend",
)

resend_rate_limit_reset = Gauge(
    "resend_rate_limit_reset",
    "Unix timestamp when rate limit resets",
)

email_send_by_error_type = Counter(
    "email_send_failure_total",
    "Total number of email send failures by error type",
    ["error_type"],
)

email_health_check_total = Counter(
    "email_health_check_total",
    "Total number of health check attempts",
    ["status"],
)
