class Error(Exception):
    pass


class LoginError(Error):
    @property
    def message(self):
        return 'User {0} login failed.'


class RecordNotFoundError(Error):
    @property
    def message(self):
        return 'Record {0} not found.'


class ProblemNotFoundError(Error):
    @property
    def message(self):
        return 'Problem {0} not found.'


class TestDataNotFoundError(Error):
    @property
    def message(self):
        return 'Test data {0} not found.'
