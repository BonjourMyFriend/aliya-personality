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
from state import AliyaState
from timing import TypingSimulator


class ChatEngine:
    """Manages LLM API calls (OpenAI-compatible), streaming, and sentence-by-sentence delivery."""

    def __init__(self, memory: Memory, state: AliyaState):
        self.memory = memory
        self.state = state

        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

        self.sim = TypingSimulator()
        self.system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        self._response_queue: queue.Queue = queue.Queue()
        self._streaming = False

    def start_response(self, user_message: str, session_id: str, ui_callback):
        """Start generating Aliya's response in a background thread.

        Returns (queue, should_skip) where should_skip is True if Aliya is
        sleeping or otherwise shouldn't respond.
        """
        # Check if Aliya is sleeping — skip LLM call
        activity = self.state.get_activity()
        if activity == "sleeping":
            self._response_queue = queue.Queue()
            self._response_queue.put({"type": "sleeping"})
            return self._response_queue

        # Check if summarization needed
        self.memory.summarize(
            session_id, self.client, SUMMARY_MODEL, SUMMARY_THRESHOLD_CHARS
        )

        # Build context with state injection
        system, messages = self._build_augmented_context(session_id)

        self._streaming = True
        self._response_queue = queue.Queue()

        # Mark any recent event as consumed before generating response
        recent_event = self.memory.get_recent_event()
        if recent_event:
            self.memory.mark_event_consumed(recent_event["id"])

        thread = threading.Thread(
            target=self._stream_worker,
            args=(system, messages, session_id),
            daemon=True,
        )
        thread.start()

        return self._response_queue

    def _build_augmented_context(self, session_id: str) -> tuple[str, list[dict]]:
        """Build the full system prompt: base + state injection + summary + recent messages."""
        summary = self.memory.get_latest_summary(session_id)
        recent = self.memory.get_recent_messages(session_id, RECENT_TURNS_IN_CONTEXT * 2)

        # Start with base system prompt
        full_system = self.system_prompt

        # Replace relationship placeholder with dynamic description
        rel_desc = self.state.get_relationship_description()
        full_system = full_system.replace("{{RELATIONSHIP_DESCRIPTION}}", rel_desc)

        # Inject Aliya's current state
        state_block = self.state.build_prompt_block()
        full_system += f"\n\n{state_block}"

        # Add conversation memory summary
        if summary:
            full_system += f"\n\n## Conversation Memory\n{summary}"

        return full_system, recent

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
