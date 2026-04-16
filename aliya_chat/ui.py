import queue
import re
from datetime import datetime

import customtkinter as ctk
from PIL import Image

from config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, PORTRAITS_DIR
from timing import TypingSimulator


# ── Chat Bubble ──

class ChatBubble(ctk.CTkFrame):
    """A single message bubble — left-aligned for Aliya, right-aligned for user."""

    def __init__(self, master, text: str, is_user: bool, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        if is_user:
            bubble_color = COLORS["user_bubble"]
            text_color = COLORS["text_primary"]
            bubble = ctk.CTkFrame(self, fg_color=bubble_color, corner_radius=14)
            bubble.grid(row=0, column=1, sticky="e", padx=(80, 10), pady=2)
        else:
            bubble_color = COLORS["aliya_bubble"]
            text_color = COLORS["text_primary"]
            bubble = ctk.CTkFrame(self, fg_color=bubble_color, corner_radius=14)
            bubble.grid(row=0, column=0, sticky="w", padx=(10, 80), pady=2)

        # Message text
        msg_label = ctk.CTkLabel(
            bubble,
            text=text,
            text_color=text_color,
            font=ctk.CTkFont(size=13),
            wraplength=int(WINDOW_WIDTH * 0.6),
            justify="left",
            anchor="w",
        )
        msg_label.pack(padx=14, pady=(10, 2), anchor="w")

        # Timestamp
        timestamp = datetime.now().strftime("%H:%M")
        time_label = ctk.CTkLabel(
            bubble,
            text=timestamp,
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(size=9),
        )
        time_label.pack(padx=14, pady=(0, 4), anchor="e")


# ── Typing Indicator ──

class TypingIndicator(ctk.CTkFrame):
    """Animated 'Aliya is typing...' indicator."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._label = ctk.CTkLabel(
            self,
            text="Aliya is typing",
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(size=12),
        )
        self._label.pack(anchor="w", padx=14, pady=4)
        self._dot_count = 0
        self._running = False
        self._job_id = None

    def start(self):
        self._running = True
        self._animate()

    def stop(self):
        self._running = False
        if self._job_id:
            self.after_cancel(self._job_id)
            self._job_id = None

    def _animate(self):
        if not self._running:
            return
        self._dot_count = (self._dot_count + 1) % 4
        dots = "." * self._dot_count + " " * (3 - self._dot_count)
        self._label.configure(text=f"Aliya is typing{dots}")
        self._job_id = self.after(400, self._animate)


# ── Chat Area ──

class ChatArea(ctk.CTkScrollableFrame):
    """Scrollable message list with auto-scroll."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._message_count = 0

    def add_bubble(self, text: str, is_user: bool) -> ChatBubble:
        bubble = ChatBubble(self, text=text, is_user=is_user)
        bubble.grid(row=self._message_count, column=0, sticky="ew", padx=4, pady=1)
        self._message_count += 1
        self._scroll_bottom()
        return bubble

    def show_typing(self) -> TypingIndicator:
        indicator = TypingIndicator(self)
        indicator.grid(row=self._message_count, column=0, sticky="w", padx=4, pady=2)
        indicator.start()
        self._scroll_bottom()
        return indicator

    def remove_widget(self, widget):
        widget.destroy()

    def _scroll_bottom(self):
        self.update_idletasks()
        self.after(10, lambda: self._parent_canvas.yview_moveto(1.0))


# ── Input Bar ──

class InputBar(ctk.CTkFrame):
    """Text input + send button. Can be locked during Aliya's response."""

    def __init__(self, master, on_send, **kwargs):
        super().__init__(master, fg_color=COLORS["frame"], height=50, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self._on_send = on_send

        self.entry = ctk.CTkEntry(
            self,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            corner_radius=20,
            height=40,
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=8)
        self.entry.bind("<Return>", lambda e: self._send())

        self.send_btn = ctk.CTkButton(
            self,
            text="Send",
            width=60,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#ffffff",
            corner_radius=20,
            command=self._send,
        )
        self.send_btn.grid(row=0, column=1, padx=(5, 10), pady=8)

    def _send(self):
        text = self.entry.get().strip()
        if text:
            self.entry.delete(0, "end")
            self._on_send(text)

    def lock(self):
        self.entry.configure(state="disabled")
        self.send_btn.configure(state="disabled")

    def unlock(self):
        self.entry.configure(state="normal")
        self.send_btn.configure(state="normal")
        self.entry.focus()


# ── Main Window ──

class AliyaWindow(ctk.CTk):
    """The main chat window."""

    def __init__(self, chat_engine, memory, session_id, state, offline_messages=None):
        super().__init__()

        self.chat_engine = chat_engine
        self.memory = memory
        self.session_id = session_id
        self._aliya_state = state  # 注意：不能用 self.state，会覆盖 tkinter 的 state() 方法
        self.sim = TypingSimulator()
        self._offline_messages = offline_messages or []

        # Generation counter — prevents stale callbacks from old responses
        self._response_gen = 0

        # Queue for proactive messages from the god module (background thread)
        self._proactive_queue: queue.Queue = queue.Queue()

        # Window setup
        self.title("Aliya")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.configure(fg_color=COLORS["bg"])

        # Build UI
        self._build_header()
        self._build_chat_area()
        self._build_input_bar()

        # Load existing conversation
        self._load_history()

        # Show offline messages if any
        self._show_offline_messages()

        # Focus input
        self.input_bar.entry.focus()

        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["frame"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Portrait
        portrait_path = PORTRAITS_DIR / "A_00.png"
        if portrait_path.exists():
            img = Image.open(portrait_path).resize((36, 36))
            self._portrait_img = ctk.CTkImage(
                light_image=img, dark_image=img, size=(36, 36)
            )
            portrait_label = ctk.CTkLabel(
                header, image=self._portrait_img, text=""
            )
            portrait_label.pack(side="left", padx=(10, 8), pady=7)

        # Name
        name_label = ctk.CTkLabel(
            header,
            text="Aliya",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        name_label.pack(side="left", pady=7)

        # Ship time
        self._time_label = ctk.CTkLabel(
            header,
            text=self._ship_time(),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
        )
        self._time_label.pack(side="right", padx=10, pady=7)
        self._update_time()

    def _ship_time(self) -> str:
        ship_time = self._aliya_state.get_ship_time()
        return f"Ship Time: {ship_time.strftime('%H:%M')}"

    def _update_time(self):
        self._time_label.configure(text=self._ship_time())
        self.after(60000, self._update_time)

    def _build_chat_area(self):
        self.chat_area = ChatArea(
            self,
            fg_color=COLORS["bg"],
            corner_radius=0,
        )
        self.chat_area.pack(fill="both", expand=True, padx=0, pady=0)

    def _build_input_bar(self):
        self.input_bar = InputBar(self, on_send=self._on_user_send)
        self.input_bar.pack(fill="x")

    def _load_history(self):
        recent = self.memory.get_recent_messages(self.session_id, limit=100)
        for msg in recent:
            is_user = msg["role"] == "user"
            self.chat_area.add_bubble(msg["content"], is_user=is_user)

    def _show_offline_messages(self):
        """展示离线期间 Aliya 留的消息。"""
        if not self._offline_messages:
            return

        # Add them to the chat area as Aliya bubbles
        for msg in self._offline_messages:
            self.chat_area.add_bubble(msg["content"], is_user=False)

        # Also store them in the database
        for msg in self._offline_messages:
            self.memory.add_message(self.session_id, "assistant", msg["content"])

    # ── Message Flow ──

    def _on_user_send(self, text: str):
        # Bump generation — any old callbacks will see a mismatch and bail
        self._response_gen += 1
        gen = self._response_gen

        # Show user bubble
        self.chat_area.add_bubble(text, is_user=True)

        # Store user message in DB first (always, even if Aliya is sleeping)
        self.memory.add_message(self.session_id, "user", text)

        # Track relationship
        from datetime import datetime
        self.memory.increment_turns()
        today = datetime.now().strftime("%Y-%m-%d")
        self.memory.log_active_day(today)

        # Check if Aliya is sleeping
        if self._aliya_state.get_activity() == "sleeping":
            # Don't lock input, don't show typing — just silently save
            return

        # Lock input
        self.input_bar.lock()

        # Show typing indicator
        self._typing_indicator = self.chat_area.show_typing()

        # "Read and think" delay, then start streaming
        think_delay = self.sim.delay_before_responding(text)
        self.after(
            int(think_delay * 1000),
            lambda: self._start_streaming(text, gen),
        )

    def _start_streaming(self, user_message: str, gen: int):
        # If a new message was sent, stop processing the old one
        if gen != self._response_gen:
            return

        # Remove the "thinking" typing indicator
        if self._typing_indicator:
            self.chat_area.remove_widget(self._typing_indicator)
            self._typing_indicator = None

        # Show real typing indicator
        self._typing_indicator = self.chat_area.show_typing()

        # Start API call
        self._queue = self.chat_engine.start_response(
            user_message, self.session_id, None
        )

        # State for this response
        self._buffer = ""
        self._sentences_ready = []
        self._stream_done = False
        self._displaying = False
        self._current_gen = gen

        # Start polling the queue
        self._poll_stream(gen)

    def _poll_stream(self, gen: int):
        if gen != self._response_gen:
            return

        try:
            while True:
                msg = self._queue.get_nowait()

                if msg["type"] == "chunk":
                    self._buffer += msg["text"]
                    self._extract_sentences()

                elif msg["type"] == "stream_done":
                    self._stream_done = True
                    remaining = self._buffer.strip()
                    if remaining:
                        self._sentences_ready.append(remaining)
                        self._buffer = ""

                elif msg["type"] == "sleeping":
                    # Aliya is asleep — remove typing indicator, unlock input
                    if self._typing_indicator:
                        self.chat_area.remove_widget(self._typing_indicator)
                        self._typing_indicator = None
                    self.input_bar.unlock()
                    return

                elif msg["type"] == "error":
                    self._stream_done = True
                    if self._typing_indicator:
                        self.chat_area.remove_widget(self._typing_indicator)
                        self._typing_indicator = None
                    self.chat_area.add_bubble(
                        "[Connection error, try again]", is_user=False
                    )
                    self.input_bar.unlock()
                    return

        except queue.Empty:
            pass

        if self._sentences_ready and not self._displaying:
            self._display_next_sentence(gen)

        if not self._stream_done or self._sentences_ready or self._displaying:
            self.after(50, lambda: self._poll_stream(gen))

    def _extract_sentences(self):
        parts = re.split(r'(?<=[.!?~])\s+|\n', self._buffer)

        if len(parts) > 1:
            for part in parts[:-1]:
                part = part.strip()
                if part:
                    self._sentences_ready.append(part)
            self._buffer = parts[-1]

    def _display_next_sentence(self, gen: int):
        if gen != self._response_gen:
            return

        if not self._sentences_ready:
            self._displaying = False

            if self._stream_done:
                if self._typing_indicator:
                    self.chat_area.remove_widget(self._typing_indicator)
                    self._typing_indicator = None
                self.input_bar.unlock()
            return

        self._displaying = True
        sentence = self._sentences_ready.pop(0)

        # Remove old typing indicator
        if self._typing_indicator:
            self.chat_area.remove_widget(self._typing_indicator)
            self._typing_indicator = None

        # Show the sentence
        self.chat_area.add_bubble(sentence, is_user=False)

        # Show typing indicator if more sentences are coming
        if self._sentences_ready or not self._stream_done:
            self._typing_indicator = self.chat_area.show_typing()

        # Calculate delay before next sentence
        typing_time = self.sim.total_typing_time(sentence)
        pause = self.sim.delay_between_sentences(sentence)
        total_delay = int((typing_time + pause) * 1000)

        self.after(
            total_delay,
            lambda: self._display_next_sentence(gen),
        )

    def _on_close(self):
        # 只记录关闭时间，不 deactivate session（保持 session 活跃以便下次恢复）
        self.memory.record_shutdown()
        self.destroy()
