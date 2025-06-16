By default fetch mail and sending mail are INFO logs this module ensures they're logged as ERROR.
This is useful when using Sentry or Loki and you want to capture (outgoing / incoming) mail server fails
