By default fetch mail and sending mail are INFO logs this module ensures they're logged as WARN.
This is useful when using Sentry and you want to capture (outgoing / incoming) mail server fails
