import av

from rounds.constants.voice import LIVE_RATE, STREAM_RATE

# 16-bit samples: two bytes each.
SAMPLE_BYTES = 2


def pcm_frame(pcm: bytes, rate: int) -> av.AudioFrame:
    """16-bit mono PCM as a frame PyAV can resample; ValueError for an odd number of bytes."""
    if len(pcm) % SAMPLE_BYTES:
        raise ValueError("Half a sample")

    frame = av.AudioFrame(format="s16", layout="mono", samples=len(pcm) // SAMPLE_BYTES)
    frame.sample_rate = rate
    frame.planes[0].update(pcm)

    return frame


def frame_bytes(frames: list[av.AudioFrame]) -> bytes:
    """Resampled frames' samples, without their buffers' padding."""
    return b"".join(bytes(frame.planes[0])[: frame.samples * SAMPLE_BYTES] for frame in frames)


def live_resampler():
    """Turns the browser's PCM (STREAM_RATE) into OpenAI's (LIVE_RATE), chunk by chunk, keeping
    the filter's state between chunks: `resample(pcm)` gives what's ready, `resample(None)` the
    rest, at the answer's end."""
    resampler = av.AudioResampler(format="s16", layout="mono", rate=LIVE_RATE)

    def resample(pcm: bytes | None) -> bytes:
        return frame_bytes(resampler.resample(None if pcm is None else pcm_frame(pcm, STREAM_RATE)))

    return resample


def stream_seconds(size: int) -> float:
    """How long `size` bytes of the browser's PCM last."""
    return size / SAMPLE_BYTES / STREAM_RATE
