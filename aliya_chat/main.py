"""
Aliya Chat — Bring the game character to life.

Usage:
  1. Put your API key in ../.env  (API_KEY=sk-...)
  2. pip install customtkinter pillow openai python-dotenv
  3. python main.py
"""
import random
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# Load .env before importing config
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from config import DB_PATH, API_KEY
from memory import Memory
from state import AliyaState
from god import God
from chat_engine import ChatEngine
from ui import AliyaWindow


# ── Relationship Phase Advancement ──

PHASE_REQUIREMENTS = {
    # target_phase: (min_days, min_turns, min_active_days)
    2: (3, 10, 2),    # Stranger → Acquaintance
    3: (14, 30, 5),   # Acquaintance → Friend
    4: (45, 80, 15),  # Friend → Close friend
}


def _check_phase_advancement(memory: Memory):
    """检查是否满足关系阶段推进条件。"""
    rel = memory.get_relationship()
    if not rel:
        return

    current_phase = rel["phase"]
    if current_phase >= 4:
        return

    target_phase = current_phase + 1
    if target_phase not in PHASE_REQUIREMENTS:
        return

    req_days, req_turns, req_active = PHASE_REQUIREMENTS[target_phase]

    # Calculate days since first interaction
    first_date = rel["first_interaction_date"]
    if not first_date:
        return

    try:
        first_dt = datetime.strptime(first_date, "%Y-%m-%d")
        today = datetime.now()
        elapsed_days = (today - first_dt).days
    except ValueError:
        return

    total_turns = rel["total_conversation_turns"]
    active_days = rel["active_days"]

    if elapsed_days >= req_days and total_turns >= req_turns and active_days >= req_active:
        memory.update_phase(target_phase)
        phase_names = {2: "Acquaintance", 3: "Friend", 4: "Close friend"}
        print(f"[Relationship] Advanced to phase {target_phase} ({phase_names.get(target_phase, 'Unknown')})")


def main():
    if not API_KEY or API_KEY == "your_api_key_here":
        print("ERROR: Set your API_KEY in the .env file!")
        print(f"  Edit: {Path(__file__).parent.parent / '.env'}")
        sys.exit(1)

    # Initialize storage
    memory = Memory(DB_PATH)

    # Initialize Aliya's state
    state = AliyaState(memory)

    # Initialize God module
    god = God(memory)

    # Initialize relationship record if first run
    today = datetime.now().strftime("%Y-%m-%d")
    memory.init_relationship(today)

    # Ensure today's schedule exists
    ship_date = god.get_ship_date()
    god.ensure_schedule_exists(ship_date)

    # Check relationship phase advancement
    _check_phase_advancement(memory)

    # ── 回溯：离线期间发生了什么 ──
    offline_messages = []
    last_shutdown = memory.get_last_shutdown()
    if last_shutdown:
        offline_messages = god.catch_up(last_shutdown)
        if offline_messages:
            print(f"Offline catch-up: {len(offline_messages)} message(s)")

    # Get or create session
    session_id = memory.get_active_session()
    if session_id is None:
        session_id = memory.create_session("Chat")

    # Initialize chat engine (with state injection)
    engine = ChatEngine(memory, state)

    # Log current ship time for debugging
    ship_time = state.get_ship_time_str()
    activity = state.get_activity()
    mood = state.get_mood_today()
    print(f"Ship Time: {ship_time} | Activity: {activity} | Mood: {mood}")

    # Launch UI
    window = AliyaWindow(engine, memory, session_id, state, offline_messages)

    # Start background god dice thread (proactive events)
    stop_event = threading.Event()

    def god_dice_loop():
        """Background thread: roll for random events, store in DB only.
        
        骰子结果只记录到数据库，不弹窗给用户。
        事件会在用户和 Aliya 聊天时，通过 system prompt 注入，
        让 Aliya 自然地提起。
        """
        if stop_event.wait(timeout=random.uniform(1200, 2400)):
            return

        while not stop_event.is_set():
            if state.get_activity() != "sleeping":
                event = god.roll_event_dice()
                if event:
                    # 只记录到数据库，不弹窗
                    memory.log_event(
                        event["seed_id"], event["event_type"], event["context"]
                    )
                    print(f"[God] Event recorded: [{event['event_type']}] {event['context'][:60]}...")

            if stop_event.wait(timeout=random.uniform(1800, 5400)):
                return

    dice_thread = threading.Thread(target=god_dice_loop, daemon=True)
    dice_thread.start()

    window.mainloop()

    # Signal dice thread to stop
    stop_event.set()

    # Record shutdown time for next session's catch-up
    memory.record_shutdown()


if __name__ == "__main__":
    main()
