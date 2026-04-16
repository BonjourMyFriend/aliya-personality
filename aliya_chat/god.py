"""
God Module — 观察的上帝。

决定 Aliya 每天的命运：
- 每日日程（起床时间、睡觉时间、情绪基调、工作内容）
- 随机事件骰子
- 用 Python 随机函数实现，不需要 LLM
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from config import SEEDS_PATH, SHIP_TIME_OFFSET_HOURS
from memory import Memory


class God:
    """观察的上帝 — 决定 Aliya 的日常和命运。"""

    # 概率常量
    MOOD_NORMAL_THRESHOLD = 0.60
    MOOD_LOW_THRESHOLD = 0.85
    STAYING_UP_PROBABILITY = 0.10
    NO_EVENT_PROBABILITY = 0.70
    EVENT_TYPE_DAILY = 0.60
    EVENT_TYPE_WORK = 0.80
    EVENT_TYPE_EMOTIONAL = 0.97
    DEFAULT_EVENT_WEIGHT = 5

    def __init__(self, memory: Memory):
        self.memory = memory
        self.seeds = self._load_seeds()

    def _load_seeds(self) -> list[dict]:
        """加载情境种子库。"""
        if not SEEDS_PATH.exists():
            return []
        with open(SEEDS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # ── 每日日程 ──

    def generate_daily_schedule(self, date: str) -> dict:
        """生成某一天的日程。

        Args:
            date: Aliya 的日期，如 "2026-04-16"
        """
        # 起床时间：10:00-12:00 随机
        wake_hour = random.randint(10, 11)
        wake_min = random.randint(0, 59)
        wake_time = f"{wake_hour:02d}:{wake_min:02d}"

        # 睡觉时间：03:00-05:00 随机
        sleep_hour = random.randint(3, 4)
        sleep_min = random.randint(0, 59)
        sleep_time = f"{sleep_hour:02d}:{sleep_min:02d}"

        # 情绪基调
        mood_roll = random.random()
        if mood_roll < self.MOOD_NORMAL_THRESHOLD:
            mood = "normal"
        elif mood_roll < self.MOOD_LOW_THRESHOLD:
            mood = "low"
        else:
            mood = "high"

        # 熬夜（10% 概率）
        is_staying_up = random.random() < self.STAYING_UP_PROBABILITY
        if is_staying_up:
            # 熬夜的话推迟 1-2 小时
            extra_hour = random.randint(1, 2)
            sleep_hour_new = sleep_hour + extra_hour
            if sleep_hour_new >= 24:
                sleep_hour_new -= 24
            sleep_time = f"{sleep_hour_new:02d}:{sleep_min:02d}"

        # 工作内容（从 work 类型的种子中选）
        work_seeds = [s for s in self.seeds if s["type"] == "work"]
        work_seed = random.choice(work_seeds) if work_seeds else None

        schedule = {
            "wake_time": wake_time,
            "sleep_time": sleep_time,
            "mood": mood,
            "work_seed_id": work_seed["id"] if work_seed else None,
            "work_description": work_seed["context"] if work_seed else "general ship maintenance",
            "is_staying_up": is_staying_up,
        }

        # 持久化
        self.memory.save_schedule(date, schedule)
        return schedule

    def ensure_schedule_exists(self, date: str) -> dict:
        """确保某天的日程已生成，没有则生成。"""
        existing = self.memory.get_today_schedule(date)
        if existing:
            return existing
        return self.generate_daily_schedule(date)

    # ── 随机事件骰子 ──

    def roll_event_dice(self) -> dict | None:
        """投骰子决定是否触发随机事件。

        Returns:
            事件字典 {seed_id, event_type, context} 或 None（什么都没发生）
        """
        # 概率权重
        roll = random.random()
        if roll < self.NO_EVENT_PROBABILITY:
            # 70% 概率：什么都没发生
            return None

        # 决定事件类型
        type_roll = random.random()
        if type_roll < self.EVENT_TYPE_DAILY:
            event_type = "daily"
        elif type_roll < self.EVENT_TYPE_WORK:
            event_type = "work"
        elif type_roll < self.EVENT_TYPE_EMOTIONAL:
            event_type = "emotional"
        else:
            event_type = "danger"

        # 从对应类型的种子中选
        matching = [s for s in self.seeds if s["type"] == event_type]
        if not matching:
            return None

        # 按权重选择
        weights = [s.get("weight", self.DEFAULT_EVENT_WEIGHT) for s in matching]
        seed = random.choices(matching, weights=weights, k=1)[0]

        return {
            "seed_id": seed["id"],
            "event_type": seed["type"],
            "context": seed["context"],
        }

    # ── 时间工具 ──

    def get_ship_time(self) -> datetime:
        """返回当前 Aliya 船时。"""
        return datetime.now() - timedelta(hours=SHIP_TIME_OFFSET_HOURS)

    def get_ship_date(self) -> str:
        """返回当前 Aliya 船时的日期。"""
        return self.get_ship_time().strftime("%Y-%m-%d")

    # ── 关机回溯 ──

    def catch_up(self, last_seen: str) -> list[dict]:
        """回溯从 last_seen 到现在之间发生了什么。

        Args:
            last_seen: ISO 格式的时间字符串，上次程序关闭的时间

        Returns:
            离线消息列表（最多 5 条），格式:
            [{"content": "...", "timestamp": "...", "type": "daily|event|emotional"}]
        """
        try:
            last_dt = datetime.fromisoformat(last_seen)
        except (ValueError, TypeError):
            return []

        now = datetime.now()
        hours_offline = (now - last_dt).total_seconds() / 3600

        if hours_offline < 0.5:
            # 离线不到 30 分钟，不需要回溯
            return []

        messages = []

        # 1. 确保离线期间每天的日程都已生成
        current = last_dt
        while current <= now:
            ship_date = (current - timedelta(hours=SHIP_TIME_OFFSET_HOURS)).strftime("%Y-%m-%d")
            self.ensure_schedule_exists(ship_date)
            current += timedelta(days=1)

        # 2. 模拟随机事件（抽样，不是每个骰子都算）
        #    大约每 2 小时一次骰子，最多检查 20 次
        num_rolls = min(int(hours_offline / 2), 20)
        pending_events = []
        for _ in range(num_rolls):
            event = self.roll_event_dice()
            if event:
                # 记录到数据库
                self.memory.log_event(
                    event["seed_id"], event["event_type"],
                    event["context"], was_offline=True
                )
                pending_events.append(event)

        # 3. 决定哪些事件值得写成离线消息
        #    优先：emotional > daily > work
        #    最多选 2 个事件
        priority = {"emotional": 0, "daily": 1, "work": 2}
        pending_events.sort(key=lambda e: priority.get(e["event_type"], 3))
        selected_events = pending_events[:2]

        for event in selected_events:
            messages.append({
                "content": event["context"],
                "timestamp": now.isoformat(),
                "type": event["event_type"],
            })

        # 4. 如果离线跨过了 Aliya 的睡觉时间，加一条"晚安"或"早安"
        if hours_offline > 8:
            # 可能跨过了整个夜晚
            ship_now = self.get_ship_time()
            ship_hour = ship_now.hour
            if 5 <= ship_hour < 12:
                messages.append({
                    "content": "刚睡醒...嗯，你来了吗",
                    "timestamp": now.isoformat(),
                    "type": "wake",
                })
            elif ship_hour >= 22 or ship_hour < 5:
                messages.append({
                    "content": "晚安...好困",
                    "timestamp": now.isoformat(),
                    "type": "sleep",
                })

        # 5. 如果离线超过 2 天，加一条关心的消息
        if hours_offline > 48:
            messages.append({
                "content": "你最近很忙吗？没事...就是随便问问",
                "timestamp": now.isoformat(),
                "type": "missed",
            })

        # 6. 如果什么都没发生，但离线超过 12 小时，至少留一条
        if not messages and hours_offline > 12:
            ship_now = self.get_ship_time()
            ship_hour = ship_now.hour
            if 22 <= ship_hour or ship_hour < 5:
                messages.append({
                    "content": "嗯...今天没什么特别的。晚安",
                    "timestamp": now.isoformat(),
                    "type": "daily",
                })
            else:
                messages.append({
                    "content": "今天挺安静的",
                    "timestamp": now.isoformat(),
                    "type": "daily",
                })

        # 硬上限 5 条
        return messages[:5]
