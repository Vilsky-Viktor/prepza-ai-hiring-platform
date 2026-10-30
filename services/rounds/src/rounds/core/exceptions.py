class SpeechFailed(Exception):
    """The speech model reported an error, or its reading strayed from the text
    (services/voice_clips.py). `seconds`: the speech made for it all the same, which is paid for."""

    def __init__(self, reason: str, seconds: float = 0.0):
        super().__init__(reason)
        self.seconds = seconds
