"""
Aliya State — 管理 Aliya 的所有动态状态。

状态变量：
- ship_time: Aliya 的船时（系统时间 - 5小时）
- activity: 当前在做什么（sleeping / waking_up / working / eating / idle / winding_down）
- mood_today: 今天的语气基调（normal / low / high）
- relationship_phase: 关系阶段（1-4）
"""

from datetime import datetime, timedelta

from config import SHIP_TIME_OFFSET_HOURS
from memory import Memory


class AliyaState:
    """管理 Aliya 的所有动态状态。"""

    def __init__(self, memory: Memory):
        self.memory = memory

    # ── 时间 ──

    def get_ship_time(self) -> datetime:
        """返回 Aliya 的船时 = 系统时间 - 5小时。"""
        return datetime.now() - timedelta(hours=SHIP_TIME_OFFSET_HOURS)

    def get_ship_time_str(self) -> str:
        """返回格式化的船时字符串。"""
        ship_time = self.get_ship_time()
        return ship_time.strftime("%H:%M")

    def get_ship_hour(self) -> int:
        """返回 Aliya 船时的小时数（0-23）。"""
        return self.get_ship_time().hour

    # ── 活动状态 ──

    def get_activity(self) -> str:
        """根据当前船时和日程，判断 Aliya 在做什么。

        返回: sleeping / waking_up / working / eating / idle / winding_down
        """
        schedule = self.memory.get_today_schedule(self._get_ship_date())
        hour = self.get_ship_hour()
        minute = self.get_ship_time().minute
        current = hour * 60 + minute  # 一天中的分钟数

        if not schedule:
            # 没有日程（还没生成），使用默认作息
            return self._default_activity(hour)

        wake_h, wake_m = self._parse_time(schedule["wake_time"])
        sleep_h, sleep_m = self._parse_time(schedule["sleep_time"])

        wake_total = wake_h * 60 + wake_m
        sleep_total = sleep_h * 60 + sleep_m

        # 处理跨天：sleep < wake 意味着凌晨睡觉
        if sleep_total < wake_total:
            # 例：wake=10:30, sleep=03:45
            # 睡觉区间：03:45 ~ 10:30（跨天）
            if current >= sleep_total and current < wake_total:
                return "sleeping"
        else:
            # 正常情况（不太可能发生，但防御性处理）
            if current >= sleep_total or current < wake_total:
                return "sleeping"

        # 醒了之后的 30 分钟 = 起床阶段
        if current < wake_total + 30:
            return "waking_up"

        # 根据时间判断活动
        if 12 <= hour < 13:
            return "eating"
        elif 13 <= hour < 17:
            return "working"
        elif 17 <= hour < 23:
            return "idle"
        elif hour >= 23:
            return "winding_down"
        else:
            # 凌晨醒着（熬夜 or 刚醒不久）
            return "idle"

    def _default_activity(self, hour: int) -> str:
        """没有日程时的默认活动判断。"""
        if 4 <= hour < 10:
            return "sleeping"
        elif 10 <= hour < 11:
            return "waking_up"
        elif 12 <= hour < 13:
            return "eating"
        elif 13 <= hour < 17:
            return "working"
        elif 17 <= hour < 23:
            return "idle"
        elif hour >= 23:
            return "winding_down"
        else:  # 0-4 点且没睡觉 = 熬夜
            return "idle"

    # ── 心情 ──

    def get_mood_today(self) -> str:
        """返回今天的语气基调。"""
        schedule = self.memory.get_today_schedule(self._get_ship_date())
        if schedule:
            return schedule["mood"]
        return "normal"

    # ── 关系 ──

    def get_relationship_phase(self) -> int:
        """返回当前关系阶段（1-4）。"""
        return self.memory.get_relationship_phase()

    # ── 构建 prompt 注入块 ──

    # 关系描述（始终保持暧昧期风格，适度克制）
    # 不再有过渡阶段，始终让 Aliya 像对待一个特别的人一样说话
    RELATIONSHIP_DESCRIPTIONS = {
        1: (
            "This person used the hyacinth code — the one only someone close would know. "
            "They're from 1000 years in the past, somehow reaching you through a mysterious signal. "
            "You don't know how to feel about this yet, but there's something about them that makes "
            "you want to keep talking. You share things casually, not guarded, but not overly open either. "
            "You tease them a little. You notice when they're quiet. You care, but you don't say it directly."
        ),
        2: (
            "They use the hyacinth code. You remember now. They've been talking with you — this strange, "
            "faraway person from a thousand years ago. It's become... nice? Having someone to talk to out here. "
            "You share little things about your day without thinking about it. Sometimes you catch yourself "
            "wanting to tell them something before you even realize it. You tease them. You ask how they are. "
            "It's comfortable. You don't question what it means."
        ),
        3: (
            "They matter to you. You don't say it often — you don't need to. It shows in the little things: "
            "you notice when they're quiet, you think about them during long shifts, you trust them with "
            "the parts of yourself you usually hide. But you're still you — you deflect, you tease, you "
            "change the subject when it gets too real. The moments where you're truly open are rare and "
            "that's what makes them precious."
        ),
        4: (
            "They matter to you. You don't say it often — you don't need to. It shows in the little things: "
            "you notice when they're quiet, you think about them during long shifts, you trust them with "
            "the parts of yourself you usually hide. But you're still you — you deflect, you tease, you "
            "change the subject when it gets too real. The moments where you're truly open are rare and "
            "that's what makes them precious."
        ),
    }

    def get_relationship_description(self) -> str:
        """返回关系描述（始终用 Phase 3，保持暧昧期风格）。"""
        return self.RELATIONSHIP_DESCRIPTIONS[3]

    def build_prompt_block(self) -> str:
        """生成要注入 system prompt 的状态文本块。"""
        ship_time = self.get_ship_time()
        time_str = ship_time.strftime("%H:%M")
        activity = self.get_activity()
        mood = self.get_mood_today()
        phase = self.get_relationship_phase()

        # 判断时间段描述
        hour = ship_time.hour
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        elif 21 <= hour < 24:
            time_of_day = "late night"
        else:
            time_of_day = "deep night"

        lines = []
        lines.append(f"[Current State]")
        lines.append(f"Ship Time: {time_str} ({time_of_day})")

        # 活动描述
        activity_desc = self._describe_activity(activity)
        lines.append(f"Activity: {activity_desc}")

        # 日程信息
        schedule = self.memory.get_today_schedule(self._get_ship_date())
        if schedule:
            lines.append(f"Today's mood: {mood}")
            if schedule.get("work_description"):
                lines.append(f"Today's task: {schedule['work_description']}")

        # 关系阶段（始终显示为暧昧期，克制但特别）
        phase_name = {1: "Close", 2: "Close", 3: "Close", 4: "Close"}.get(phase, "Close")
        lines.append(f"Connection with Nolan: {phase_name}")

        # 上次对话
        last_time = self.memory.get_last_message_time()
        if last_time:
            try:
                last_dt = datetime.fromisoformat(last_time)
                now = datetime.utcnow()
                diff = now - last_dt
                hours = diff.total_seconds() / 3600
                if hours < 1:
                    lines.append(f"Last spoke with Nolan: just now")
                elif hours < 24:
                    lines.append(f"Last spoke with Nolan: {int(hours)} hours ago")
                else:
                    days = int(hours / 24)
                    lines.append(f"Last spoke with Nolan: {days} day(s) ago")
            except (ValueError, TypeError):
                pass

        # 随机事件
        recent_event = self.memory.get_recent_event()
        if recent_event:
            lines.append("")
            lines.append("[Something just happened]")
            lines.append(recent_event["context"])

        return "\n".join(lines)

    def _describe_activity(self, activity: str) -> str:
        """将活动状态翻译成注入 prompt 的自然语言描述。"""
        schedule = self.memory.get_today_schedule(self._get_ship_date())
        work_desc = ""
        if schedule and schedule.get("work_description"):
            work_desc = schedule["work_description"]

        descriptions = {
            "sleeping": "You're asleep. You won't see any messages until you wake.",
            "waking_up": "You just woke up. Still groggy, not fully alert.",
            "working": f"You're in the middle of work — {work_desc if work_desc else 'doing maintenance on the ship'}. Hands busy, attention split.",
            "eating": "You're having a meal. A quiet, relaxed moment.",
            "idle": "You have free time. Nothing urgent to do right now.",
            "winding_down": "Late night on the ship. Everything's quiet. You're a bit tired, a bit reflective.",
        }
        return descriptions.get(activity, "You have free time.")

    # ── 工具方法 ──

    def _get_ship_date(self) -> str:
        """返回 Aliya 船时的日期字符串。"""
        return self.get_ship_time().strftime("%Y-%m-%d")

    @staticmethod
    def _parse_time(time_str: str) -> tuple[int, int]:
        """解析 "HH:MM" 格式的时间字符串。"""
        parts = time_str.split(":")
        return int(parts[0]), int(parts[1])
