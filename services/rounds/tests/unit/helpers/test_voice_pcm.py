# The browser's speech as OpenAI takes it (helpers/voice_pcm.py).
import itertools
import math
import struct

import pytest

from rounds.helpers.voice_pcm import live_resampler, pcm_frame, stream_seconds


def tone(seconds: float, rate: int, hertz: float = 440) -> bytes:
    """A sine wave as 16-bit mono PCM."""
    count = int(seconds * rate)

    return struct.pack(
        f"<{count}h", *(int(8000 * math.sin(2 * math.pi * hertz * i / rate)) for i in range(count))
    )


def test_the_browsers_16_khz_frames_become_24_khz_chunk_by_chunk():
    resample = live_resampler()
    pcm = tone(1.0, 16_000)
    out = b"".join(resample(pcm[start : start + 1024]) for start in range(0, len(pcm), 1024))
    out += resample(None)

    # A second at 24 kHz, 2 bytes a sample, give or take the filter's edge.
    assert abs(len(out) - 48_000) <= 64
    samples = struct.unpack(f"<{len(out) // 2}h", out)
    # Still the same tone: about 440 crossings of zero up a second.
    rising = sum(1 for a, b in itertools.pairwise(samples) if a < 0 <= b)
    assert 435 <= rising <= 445


def test_half_a_sample_is_refused():
    with pytest.raises(ValueError):
        pcm_frame(b"\x00", 16_000)


def test_the_browsers_bytes_tell_how_long_was_said():
    assert stream_seconds(32_000) == 1.0
    assert stream_seconds(1024) == 0.032
