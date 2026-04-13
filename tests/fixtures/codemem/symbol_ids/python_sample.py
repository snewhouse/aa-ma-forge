"""Golden fixture for SCIP symbol ID grammar (Python).

Frozen — any change here requires rolling the symbol-id-grammar schema
(M1 Task 1.2b) and rerunning downstream test expectations.
"""


def foo():
    return 1


class Bar:
    def baz(self):
        return 2

    @staticmethod
    def qux():
        return 3


class Outer:
    class Inner:
        pass
