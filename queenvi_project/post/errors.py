class MediaValidationError(Exception):
    def __init__(self, ext):
        self.ext = ext
