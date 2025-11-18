class NaoMove:
    """
    This class describes the information
    of a single move.
    """
    def __init__(self, duration=None, preconditions=None, postconditions=None):
        self.duration = duration
        self.preconditions = preconditions if preconditions is not None else {}
        self.postconditions = postconditions if postconditions is not None else {}
