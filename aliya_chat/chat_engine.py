import threading
import queue

from openai import OpenAI

from config import (
    API_KEY,
    BASE_URL,
    CHAT_MODEL,
    SUMMARY_MODEL,
    MAX_TOKENS,
    SUMMARY_THRESHOLD_CHARS,
    RECENT_TURNS_IN_CONTEXT,
    SYSTEM_PROMPT_PATH,
)
from memory import Memory
from timing import TypingSimulator


class ChatEngine:
    """Manages LLM API calls (OpenAI-compatible), streaming, and sentence-by-sentence delivery."""

    def __init__(self, memory: Memory):
        self.memory = memory

        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

        self.sim = TypingSimulator()
        self.system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        self._response_queue: queue.Queue = queue.Queue()
        self._streaming = False

    def start_response(self, user_message: str, session_id: str, ui_callback):
        """Start generating Aliya's response in a background thread."""
        # Store user message
        self.memory.add_message(session_id, "user", user_message)

        # Check if summarization needed
        self.memory.summarize(
            session_id, self.client, SUMMARY_MODEL, SUMMARY_THRESHOLD_CHARS
        )

        # Build context
        system, messages = self.memory.build_context(
            session_id, self.system_prompt, RECENT_TURNS_IN_CONTEXT
        )

        self._streaming = True
        self._response_queue = queue.Queue()

        thread = threading.Thread(
            target=self._stream_worker,
            args=(system, messages, session_id),
            daemon=True,
        )
        thread.start()

        return self._response_queue

    def _stream_worker(self, system: str, messages: list[dict], session_id: str):
        """Background thread: streams response and puts chunks into queue."""
        try:
            # OpenAI format: system message as a message with role="system"
            api_messages = [{"role": "system", "content": system}] + messages

            stream = self.client.chat.completions.create(
                model=CHAT_MODEL,
                max_tokens=MAX_TOKENS,
                messages=api_messages,
                stream=True,
            )

            full_text = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_text += text
                    self._response_queue.put({"type": "chunk", "text": text})

            self._response_queue.put({"type": "stream_done", "full_text": full_text})

            # Store the complete response
            self.memory.add_message(session_id, "assistant", full_text)

        except Exception as e:
            self._response_queue.put({"type": "error", "error": str(e)})
        finally:
            self._streaming = False

    @property
    def is_streaming(self) -> bool:
        return self._streaming
