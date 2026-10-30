"""A recorded answer streamed as voice mode streams it from the browser (rounds'
services/voice_stream.py): decoded to the speech detector's 16 kHz frames, sent in real time
through rounds' own resampler and realtime transcription session, with the detector's trailing
silence (SPEECH_END_MS) before the end. Gives the text, its cost and how long the final text took
after the end, the only wait the candidate has."""

import asyncio
import time

import av
from prepza_common.ai.llm import audio_cost

from rounds.helpers.voice_pcm import frame_bytes, live_resampler
from rounds.integrations.live_hearing import live_hearing

# The detector's frame (512 samples at 16 kHz, 2 bytes each) and its silence before an end.
FRAME_BYTES = 1024
FRAME_SECONDS = 0.032
SPEECH_END_FRAMES = 650 // 32


def browser_pcm(audio_path) -> bytes:
    """A clip as the browser's frames: 16-bit mono PCM at 16 kHz."""
    resampler = av.AudioResampler(format="s16", layout="mono", rate=16_000)

    with av.open(str(audio_path)) as container:
        frames = [out for frame in container.decode(audio=0) for out in resampler.resample(frame)]

    return frame_bytes(frames + resampler.resample(None))


async def hear_live(audio_path, language: str, keywords: list[str], model: str, delay: str):
    """(text, cost, seconds from the end to the final text)."""
    pcm = browser_pcm(audio_path) + bytes(FRAME_BYTES * SPEECH_END_FRAMES)
    resample = live_resampler()

    async with live_hearing(language, keywords, model, delay) as hearing:
        for start in range(0, len(pcm), FRAME_BYTES):
            await hearing.send(resample(pcm[start : start + FRAME_BYTES]))
            await asyncio.sleep(FRAME_SECONDS)

        ended = time.monotonic()
        await hearing.send(resample(None))
        text = await hearing.final()
        waited = time.monotonic() - ended

    return text, audio_cost(model, hearing.seconds) or 0.0, waited
