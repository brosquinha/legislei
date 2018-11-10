class ModelError(Exception):
    """ Base model exception """

    def __init__(self, msg):
        self.message = msg