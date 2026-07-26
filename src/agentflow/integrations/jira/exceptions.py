class JiraError(Exception):
    pass


class JiraAuthenticationError(JiraError):
    pass


class JiraPermissionError(JiraError):
    pass


class JiraTicketNotFoundError(JiraError):
    pass


class JiraRateLimitError(JiraError):
    pass


class JiraTemporaryError(JiraError):
    pass