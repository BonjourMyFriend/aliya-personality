import random
import re
import time


class TypingSimulator:
    """Calculate realistic delays for simulating human typing/reading."""

    def __init__(self, wpm_reading: int = 230, wpm_typing: int = 90,
                 jitter: tuple[float, float] = (0.7, 1.3)):
        """Speeds tuned for chat-style messaging (fast casual typing, not formal).

        Aliya texts quickly — she's young, impatient, sends rapid bursts.
        At 90 WPM: each char ~111ms, so a 30-char sentence "types" in ~3.3s.
        The between-sentence pause (thinking time) is what makes it feel natural.
        """
        self.wpm_reading = wpm_reading
        self.wpm_typing = wpm_typing
        self.jitter = jitter

        # Milliseconds per character
        # Average English word = 5 chars + 1 space = 6 chars
        self.ms_per_char_typing = 60000 / (wpm_typing * 6)   # ~111ms
        self.ms_per_char_reading = 60000 / (wpm_reading * 6)  # ~43ms

    def delay_before_responding(self, user_message: str) -> float:
        """Seconds to wait before Aliya starts 'typing' her response.

        Simulates: reading the user's message + thinking about a reply.
        """
        char_count = len(user_message)
        read_time_ms = char_count * self.ms_per_char_reading
        think_time_ms = random.uniform(1000, 3000) + min(char_count * 5, 2000)
        return (read_time_ms + think_time_ms) / 1000.0

    def char_delay(self, char: str) -> float:
        """Delay in seconds for typing one character."""
        base = self.ms_per_char_typing / 1000.0
        jitter = random.uniform(*self.jitter)

        if char == ' ':
            return base * 0.6 * jitter
        elif char in '.!?':
            return base * 2.5 * jitter
        elif char == ',':
            return base * 1.8 * jitter
        elif char == '~':
            return base * 3.0 * jitter
        else:
            return base * jitter

    def delay_between_sentences(self, sentence: str) -> float:
        """Pause in seconds between sentence bubbles."""
        s = sentence.rstrip()

        if s.endswith('...'):
            return random.uniform(1.5, 3.5)
        elif s.endswith(('!', '?', '~')):
            return random.uniform(0.4, 1.0)
        else:
            return random.uniform(0.8, 2.0)

    def total_typing_time(self, sentence: str) -> float:
        """Total seconds to 'type' an entire sentence."""
        total = 0.0
        for char in sentence:
            total += self.char_delay(char)
        return total


def split_into_sentences(text: str) -> list[str]:
    """Split Aliya's response into individual message bubbles.

    Rules (tuned for her speech patterns):
    1. Split on \\n first (she thinks in line breaks)
    2. Split on sentence-ending punctuation (. ! ? ~)
    3. Keep ... attached to the preceding text
    4. Keep **** censorship marks intact
    """
    lines = text.strip().split('\n')
    sentences = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Split on sentence boundaries: after .!?~ followed by space
        # But keep ... intact and don't split on abbreviations
        parts = re.split(r'(?<=[.!?~])\s+', line)

        for part in parts:
            part = part.strip()
            if part:
                sentences.append(part)

    return sentences if sentences else [text.strip()]
