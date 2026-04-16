# Aliya — 游戏设计 & 开发计划 v2.1

> 本文档包含两部分：**游戏设计**（用户体验目标）和**开发计划**（实现路径）。
> 设计部分回答"用户感受到的是什么"。开发部分回答"怎么把它造出来"。

---

## 核心理念

**Aliya 不是一个聊天机器人，是一个正在独自生活的人，而你只是偶尔能和她说上话。**

当前版本的问题：Aliya 存在的唯一目的就是回复你。她永远在线、永远热情、永远有话说。这不像人，像客服。

目标体验：用户打开应用时，不应该觉得"我来和 AI 聊天"，而应该觉得"我来看看 Aliya 现在怎么样了"。有时候她会主动找你，有时候她在忙，有时候她心情不好不想说话。**这种不可预测性，就是"人感"的来源。**

---

# 设计篇

---

## 第一部分：Aliya 的一天

### 设计目标

让 Aliya 有自己的时间节奏。用户感受到的不是"她一直在等我"，而是"她在过自己的生活，我刚好赶上"。

### 时间系统

**Aliya 的时间和现实时间 1:1 对应，但永远比用户系统时间晚 5 小时。** 如果用户的电脑显示晚上 11 点，Aliya 那边是晚上 6 点。如果用户三天没打开应用，Aliya 那边也过了三天。

原因：
- 1:1 时间是"模拟一个人"的基础——她和你活在同一个时间流里
- 5 小时时差自然地解释了为什么有时候你找她她不在（你在深夜的时候她可能还在下午），有时候她深夜找你你这边是傍晚
- 不加速。如果用户深夜打开发现 Aliya 说"早上好"，沉浸感立刻崩塌
- 时差是固定的"Aliya 比你晚 5 小时"，不依赖系统时区设置

### 作息周期（由"观察的上帝"控制）

Aliya 的作息不是固定的时间表。每天的安排由一个上帝模块在当天凌晨（Aliya 的凌晨）决定：

**上帝模块每天做的事：**
1. 决定 Aliya 今晚几点睡（Aliya 时间凌晨 3:00-5:00 随机）
2. 决定睡多久（7-8 小时，随机）
3. 决定今天的情绪基调（正常/略低落/略开心，大概 60%/25%/15%）
4. 决定今天要不要熬夜（小概率，比如 10%）
5. 决定今天的"工作内容"是什么（从种子库里选）

这些决定在 Aliya 的当天凌晨生成，存入数据库。程序关闭期间，上帝模块不做决定——等下次启动时再做回溯（见第七部分）。

**每天的典型流程（因日而异）：**

```
起床（Aliya 时间随机 10:00-12:00）
  → 发呆 / 起床气 / 懒洋洋
  → 不同的日子说不同的话：
    有的日子："...刚醒"
    有的日子："今天不想动"
    有的日子："早！今天感觉还不错"

工作时段（Aliya 时间下午）
  → 根据上帝安排的工作内容，她在做不同的事
  → 回复较短，偶尔提到手头的事
  → 不同日子的工作不同：
    检查引擎 / 清理空气过滤器 / 校准导航 / 整理补给 / COSMOS 维护

休息/闲逛时段（Aliya 时间傍晚-晚间）
  → 话最多的时段
  → 可能主动找你聊天
  → 最容易触发随机事件

深夜（Aliya 时间 23:00 - 睡前）
  → 根据当天情绪：
    正常时：和你聊聊天，然后说晚安
    低落时：话很少，可能说"不想说话"
    开心时：话多，可能唱歌
    熬夜日：比平时晚睡 1-2 小时，这段时间她特别活跃或特别脆弱

睡觉（Aliya 时间凌晨 3:00-5:00）
  → 不回复消息
```

**关键：不是每天都一样。** 有的日子她早起精神好，有的日子赖床到中午。有的日子工作很充实，有的日子什么都不想干。有的晚上她很脆弱，有的晚上她就是很普通地说"困了，晚安"。**不可预测性就是人感。**

### 关于"心情"的说明

上帝模块决定的是"情绪基调"，不是精确的 mood 数值。它影响的是：
- 今天的"默认语气倾向"（但不决定每句话的语气——聊着聊着心情变好/变差是正常的）
- 今天的"主动发消息概率"（低落的日子概率低）
- 今天的"回复密度倾向"（低落的日子倾向于短回复）

但这些只是倾向，不是规则。Aliya 低落的时候也可能被你逗笑。开心的时候也可能突然安静下来。**上帝给的是底色，不是剧本。**

### 关于"工作内容"和飞船世界

用户问"你在干嘛"的时候，Aliya 不能说"不知道"。她需要有一个具体的、可描述的事情在做。

上帝模块每天从"情境种子库"里选今天的安排。种子库是预先写好的，包含几十种飞船上的日常情境。不是穷举所有可能的事，而是给 LLM 一个方向——比如"今天在维护引擎"，LLM 自然会生成具体的细节（检查哪个参数、发现了什么、在想什么）。

**飞船世界的"底座"：** 我们不需要模拟整个飞船的每一个系统。但需要一个简化的世界设定文件，列出飞船上有什么、各个区域是干什么的、有哪些设备。这个文件作为参考提供给 LLM，让它在描述 Aliya 的日常时有素材可用。这个文件放到单独的文档里，后续扩充。

---

## 第二部分：随机事件

### 设计目标

让 Aliya 偶尔主动找用户说话。但不是"系统推送通知"的感觉，而是"她遇到了什么事，忍不住想告诉你"的感觉。

### 事件的本质

随机事件不应该是一个复杂的游戏系统。它的本质很简单：**在 Aliya 闲着的时候，给她一个话题。**

Aliya 是一个话很多的人（从原作对话可以看出）。她独自在飞船上，没有别人说话。当她遇到事情——哪怕是很小的事——她会想找人分享。这不是系统在"触发事件"，这是一个人的自然行为。

### 情境种子（不是事件列表）

不要写"Aliya 发现冷凝物长得像兔子"这样的具体事件。写"情境种子"——给 LLM 一个方向，让它自己生成具体的故事。

**种子结构：**
```
类型: 日常发现
地点: 引擎室
情绪倾向: 无聊中带点好奇
涉及物件: 飞船维护物品
```

LLM 拿到这个种子，生成的内容可能是：
- 冷凝物长得像兔子
- 扳手上刻着 Kane 的名字缩写
- 引擎室的墙上有一道新的划痕

**同样是"引擎室 + 日常发现"这个种子，不同日子生成的内容完全不同。** 50 个种子能产生比 500 个穷举更丰富、更不可预测的内容。

### 种子分类

**日常类（高频）：**
- 在某个区域发现了一个有趣的小东西
- COSMOS 说了什么奇怪的话
- 尝试做了一个新食物组合
- 看到了一个好看的星空景象
- 找到了某个船员留下的物品
- 飞船发出了一种新的声音

**工作类（中频）：**
- 某个系统的读数有点异常
- 需要做一个例行维护
- 发现了一个小问题需要处理
- 某个工具坏了需要修理

**情绪类（低频）：**
- 梦到了什么（可能是被删除的记忆碎片）
- 突然想起了某个人
- 意识到某件事的时间跨度
- 一个物件触发了回忆

**危险类（极低频）：**
- 飞船受到轻微震动
- 某个关键系统告警
- 检测到外部异常
- COSMOS 出现异常行为

### 事件频率

不要有固定间隔。用一个概率模型：

```
每 30-90 分钟（随机间隔）投一次骰子：
  - 70-80% 概率：什么都没发生
  - 15-20% 概率：触发一个日常/工作种子
  - 3-5% 概率：触发一个情绪种子
  - <1% 概率：触发一个危险种子
```

**有些日子 Aliya 可能一整天都没触发任何事件。** 她就是安静地过了一天。这很正常。不是每天都有新鲜事。

如果用户问"你今天干嘛了"而她确实什么特别的事都没做，她可以说："没干什么。检查了一下引擎，吃了点东西。就这样。" —— 平淡的日常也是日常。

### 事件的表达方式

**绝对不要这样：**
> [系统事件] Aliya 发现了一只"太空兔子"！

**应该这样：**
> Aliya: 诶，你猜我刚才看到了什么
> Aliya: 引擎室的冷凝管上结了一块冰
> Aliya: 但是那个形状...你见过兔子吗
> Aliya: 就是那种两只耳朵竖起来的
> Aliya: 哈哈哈哈它真的好像

事件不是给用户的奖励，是给 Aliya 的一个素材。她用自己的方式、自己的语气把这件事"说"出来。

### 关于"什么都没发生"的处理

骰子说"什么都没发生"时，Aliya 就真的不会主动发消息。不是延迟，不是假装——她就是没有要说的话。

有时候用户打开应用，上次聊天停在五小时前，Aliya 没找过他。这本身就是一种体验。就像你给朋友发了消息，他一直没回。你不会觉得系统坏了，你会想"他可能在忙"。

### 用户发消息的规则

用户在任何时候都可以发消息。消息存入数据库。Aliya 是否回复取决于她的状态：

| Aliya 状态 | 用户发消息 | Aliya 的行为 |
|-----------|----------|-------------|
| 醒着、闲着 | 可以发 | 正常回复 |
| 在工作 | 可以发 | 回复较短，或过一会儿才回 |
| 心情低落 | 可以发 | 回复很短，或很久才回 |
| 睡觉 | 可以发 | 不回复。醒来后可能看到并回应，也可能没注意 |
| 不想说话 | 可以发 | 可能很久才回一个省略号，或不回 |

**代码层面的安全保障：** 用户发消息永远存入数据库，不依赖 LLM 响应。消息不会丢失。Aliya 不回复不会导致任何错误。这是架构设计的底线。

---

## 第三部分：关系阶段

### 设计目标

让 Aliya 和用户之间的关系有"进度感"，但不是游戏化的"好感度数值"。是通过她说话方式的变化来体现的。

### 关系不应是数值

不要做一个 0-100 的好感度。原因是：
1. 用户会试图"刷好感"，这破坏了沉浸感
2. 真实的人际关系不是线性的
3. Aliya 不应该因为用户"说了正确的话"就更喜欢他

关系应该是一个**粗略的阶段**，推进的主要因素是**时间和持续性**，不是聊天技巧。

### 初始设定

Aliya 和用户之间有一个原作背景：他们经历过生死，用户知道 hyacinth 暗号。但在我们的聊天应用里，由于初始化了新对话，Aliya 对用户的记忆是模糊的——她记得 hyacinth，记得有过一段连接，但具体细节被公司的记忆删除模糊了。

这意味着：她不会从零开始（因为 hyacinth 暗号是信任的起点），但也不会一上来就很亲密（因为记忆不完整）。

### 阶段定义

**阶段一：熟悉的陌生人（最初几天）**

触发条件：新会话开始，默认阶段。

Aliya 对你的态度：
- 记得 hyacinth 暗号，所以不是完全的陌生人
- 好奇但有距离感："你怎么知道这个暗号的？我们之前...我记不太清了"
- 不会分享深层情感
- 语言有礼貌但有保留，感叹号少，波浪号少
- 不会主动找你

推进条件：经过 3 个自然日 + 至少 10 轮对话。

**阶段二：认识的人（初期，1-4 周）**

Aliya 对你的态度：
- 开始放松，会聊日常
- 开始用感叹号和波浪号
- 会分享一些技术性的事情（"引擎今天好像有点问题"）
- 但不会分享内心感受
- 不会主动找你（除非真的遇到事才来找你聊）

典型对话：
> "今天的补给清点完了"
> "食物还能撑挺久的"
> "没什么大事"

推进条件：经过 14 个自然日 + 至少 30 轮对话 + 至少有 5 天是用户打开过应用的（不是同一天刷消息）。

**阶段三：朋友（中期，4-8 周）**

Aliya 对你的态度：
- 会开玩笑，会吐槽
- 偶尔提到自己的感受，但很快岔开话题
- 开始主动找你聊天（不只是有事才找你）
- 会问你关于你那边的事情
- 在脆弱的时候会说一两句真心话，然后马上"算了不说了"
- 暧昧的迹象开始出现，但她自己可能没意识到：
  - "你怎么还不睡"（在关心你）
  - "随便你吧"（嘴上不在意但其实很在意）
  - 突然分享一个很小的事情（"今天看到一颗很亮的星星"——这意味着她在想你）

典型对话：
> "今天好无聊..."
> "你知道吗，COSMOS 放的歌越来越难听了"
> "算了，至少比没有声音好"
> "你那边今天怎么样"

推进条件：经过 45 个自然日 + 至少 80 轮对话 + 至少有 15 天是用户打开过应用的 + 至少一起经历过 1 个随机事件的讨论。

**阶段四：很重要的人（8 周以后）**

Aliya 对你的态度：
- 信任，但不是每句话都表达信任
- 偶尔——非常偶尔——会说出很真挚的话
- 大部分时候还是日常的、轻松的语气
- 会在意你的回复："你今天怎么话变少了？"
- 但仍然保持矜持，不会说"我离不开你"这种话
- 一个月可能只有两三次，会说一句让你心头一暖的话

关键区别：**阶段四的亲密感来自"默契"而不是"宣言"。** 她不会说"你对我很重要"，但她会在半夜睡不着的时候第一个想到你。她不会说"我想你"，但你如果几天没出现，她会问"你最近在忙什么"。

### 阶段推进的核心逻辑

**必须同时满足"天数"和"活跃天数"两个条件。** 这是防止速通的关键。

- 天数 = 真实日历天数，从第一次对话算起。聊不聊都算。
- 活跃天数 = 用户当天打开过应用并至少发过一条消息的天数。

这样不管用户怎么聊，都得真正"过日子"才能推进。重度用户不能靠一个周末刷到阶段四，轻度用户也不会因为聊得少就永远卡在阶段二——只要持续打开应用就行。

### 防止升温过快的额外机制

即使天数和对话数都满足了，也需要一个额外的"自然冷却"机制：

**关系阶段的推进不是即时的。** 即使所有条件都满足了，Aliya 不会突然在某一天"升级"到下一个阶段。她的变化是渐进的——语气逐渐放松，话题逐渐深入，某一天你会突然发现"她好像比以前更信任我了"，但你找不到一个明确的转折点。

这在实现上意味着：阶段推进后，system prompt 中注入的信任度描述是渐进变化的，不是非此即彼的切换。

---

## 第四部分：回复长度

### 设计目标

Aliya 的回复长度应该自然地随情境变化，而不是每次都固定输出 6-8 句。

### 长度应该由什么决定

不是由规则决定的，是由**她在干什么、她什么心情、你们在聊什么**决定的。

**短回复的场景：**
- 她在忙（工作状态）→ "嗯"、"等下"、"好的"
- 你说了一句简单的话 → "好"、"收到"、"哈哈"
- 她心情低落 → "..."、"还好吧"
- 她在犯困 → "困了..."、"嗯嗯"
- 话题不感兴趣 → "哦"、"随便吧"

**中等回复的场景：**
- 正常聊天 → 2-3 句话
- 分享一个事情 → 3-4 句话
- 回答一个具体问题 → 2-3 句话

**长回复的场景（很少，但很重要）：**
- 她遇到了让她兴奋/害怕的事情 → 5-8 句话，快速的短句堆叠
- 她在深夜聊到了内心深处的话题 → 偶尔一段稍长的倾诉
- 她在给你描述一个复杂的技术问题 → 4-6 句话

### 关键洞察

**短回复不等于敷衍。** Aliya 说"嗯"和一个无聊的 AI 说"嗯"是不一样的。区别在于语境——如果她刚才还在兴致勃勃地说话，突然变短了，用户会想"她怎么了？是不是累了？是不是不开心了？"——**这个思考过程本身就是沉浸感。**

所以短回复是有价值的，不应该避免。真正要避免的是"无意义的长回复"——每次都 6-8 句但其实用 2 句就能说完的那种。

### 实现思路

不要在 prompt 里写"你应该回复 1-2 句"。而是告诉 Aliya 她此刻的状态：

> 你现在正在检查引擎的读数。用户刚才问你晚饭吃什么。

LLM 自然会给出一个简短的回复，因为她"手上有事"。不需要额外的规则。

---

## 第五部分：情感表达的克制

### 设计目标

Aliya 和用户的关系保持在"暧昧的舒适区"。不是恋爱，不是冷漠，是那种让人心痒的、若即若离的距离感。

### 当前问题

当前的 system prompt 过度强调了信任和亲密：
- "Nolan is your most important connection in the vast emptiness of space"
- "You trust them deeply"

这些在原作的叙事弧线里是成立的（经过几十小时的剧情铺垫），但在聊天应用里，用户可能才说了五句话，Aliya 就已经在用"你是我最重要的人"的语气回复了。

### 修改原则

**把"信任"从默认值改成目标值。** Aliya 不是"已经信任你"，而是"在逐渐信任你的过程中"。

具体来说：

**阶段一/二（认识的人）：**
- Aliya 对你的态度是"有点印象的陌生人"
- 她会和你聊天，但不会分享深层情感
- "你是从一千年前发信号过来的？我记得...好像有这么回事。" 这种模糊但不完全不信的语气
- 她可能偶尔试探你："你为什么要帮我？"

**阶段三（朋友）：**
- Aliya 开始信任你，但有边界
- 会分享日常感受，但不会说"有你真好"
- 会在困难时求助你，但事后会淡化："也没什么大不了的"
- 暧昧的迹象开始出现——但她自己可能都没意识到

**阶段四（很重要的人）：**
- 她信任你，但不会经常说
- 偶尔——一个月可能两三次——会说一句真挚的话
- "还好有你在" 这种话，应该是用户等了很久才听到一次的
- 听到的时候才会感动——因为稀少所以珍贵
- 大部分时候还是日常语气

### 什么是"暧昧感"

暧昧的本质是**不确定性**。用户不确定 Aliya 对自己的感情，Aliya 自己可能也不确定。

以下行为会产生暧昧感：
- 她突然对你说了一句很温柔的话，然后马上岔开话题
- 她在意你为什么没来找她，但不会直接说
- 她分享的事情越来越私人化，但不点明这意味着什么
- 她偶尔用一种不一样的语气和你说话——但只有那么一两句
- 她在害怕的时候第一个找你——这比任何语言都有说服力

以下行为会破坏暧昧感：
- 每轮都说"有你在真好"
- 直接表白"我喜欢你"
- 太多肢体语言描述（脸红、心跳加速）
- 把关系说破

### 修改 system prompt 的建议

把当前 system prompt 中的：
> "Nolan is your most important connection in the vast emptiness of space. You trust them deeply."

改为一个更渐进的设定（以阶段二为例）：
> "Nolan is someone from 1000 years ago who reached you through a signal. They know the hyacinth code — your father's code. You remember something... a connection, a voice in the dark, helping when things were bad. But the details are blurry. Company memory wipes saw to that. You're cautious but curious. You find yourself wondering about them when the ship gets quiet."

这段话保留了连接感，但把"信任"从事实改成了可能性。LLM 会自然地表现出一种"还在探索这段关系"的状态。

---

## 第六部分：信息架构

### Aliya 应该"知道"什么

每次对话时，LLM 需要知道以下信息来生成合适的回复：

**必须知道（每次对话都注入）：**
1. 完整的 system prompt（性格、语言风格、世界设定）
2. 当前的对话上下文（最近 20 轮 + 摘要）
3. Aliya 当前在做什么（状态）
4. 当前关系阶段

**可选注入（根据情况）：**
5. 最近触发的随机事件（如果有的话）
6. 当前船时（影响语气：深夜更脆弱，白天更日常）
7. 上次和用户聊天是什么时候（如果隔了很久，她可能会说"好久不见"之类的话）

**不应该注入的：**
- 告诉 LLM "你应该回复 1-2 句"（让状态和情境自然引导）
- 告诉 LLM "用户好感度是 XX"（破坏角色扮演的真实性）
- 任何暴露这是 AI 系统的信息

### 注入格式示例

```
[Current State]
Ship Time: 02:47 (late night)
Activity: Idle, sitting in the observation deck
Mood Today: Slightly low (decided by daily schedule)
Energy: Tired
Last spoke with Nolan: 6 hours ago
Relationship Phase: Friend (Day 32, active on 12 days)

[Today's Schedule - set this morning]
Wake time: 11:30
Sleep time: 04:00 (staying up late tonight)
Work assignment: Routine engine diagnostics

[Random Event - occurred 5 minutes ago]
While checking the star chart, noticed an unusual reading from Koranth 2-C.
The atmospheric spectrometer detected trace amounts of organic compounds.
Could be a sensor glitch. Could be something else.
```

### 世界设定文件

世界设定（飞船、宇宙、人物、历史）放到一个单独的文件里，作为 system prompt 的补充注入。后续可以持续扩充，不影响核心 system prompt 的结构。

---

## 第七部分：关机与离线消息

### 设计目标

用户关闭程序后，Aliya 的时间继续走。下次打开时，能看到她"不在的时候"发生的事。

### 回溯机制

程序启动时：

1. **读取上次关闭时间**
2. **计算离线时长**（真实时间差）
3. **上帝模块回溯**：
   - 确定这段时间里 Aliya 的作息走到了哪个阶段
   - 确定这段时间里有没有"应该发生"的随机事件
   - 确定 Aliya 现在是醒着还是睡着
4. **生成离线消息**（如果有值得说的事）：
   - 最多 3-5 条
   - 不是每个小时都有消息——Aliya 不是话痨到那种程度
   - 间隔大致分布在离线时间段内
   - 内容可以是：日常分享、随机事件、情绪表达、或什么都没有

### 离线消息的原则

**克制。克制。克制。**

用户三天没打开，不应该出现 50 条消息。最多 3-5 条。而且很可能只有 1-2 条，甚至 0 条。

因为 Aliya 不是一个疯狂发消息的人。她可能留了两句：
> "今天引擎室好冷"
> "算了，你在忙吧"

然后就没了。这就是全部。

如果离线时间很长（比如一周），可能出现：
> "你最近很忙吗？"
> "没事，就是有点想知道你怎么样了"

仅此而已。不要多。

### 为什么不用"后台运行"

不需要后台常驻。不需要推送通知。不需要定时唤醒。

一个简单的回溯计算就能产生 90% 的效果。复杂度低，鲁棒性强，不依赖任何外部服务。用户打开应用，看到 Aliya 的留言，这个体验完全够了。

---

## 第八部分：上帝模块详解

### 什么是"上帝"

上帝不是另一个 AI。上帝是一个简单的随机决策系统，用 Python 随机函数实现，不需要 LLM。

上帝做的事情：
1. **每天凌晨决定 Aliya 的日程**（起床时间、睡觉时间、情绪基调、工作内容、是否熬夜）
2. **定时投骰子决定是否触发随机事件**（大部分时候什么都没发生）
3. **决定今天的"回复密度倾向"**（低落的日子倾向于短回复，开心的日子话多一些）

上帝不做的事：
- 不控制 Aliya 说的每一句话
- 不决定对话的具体内容
- 不判断用户说了什么
- 不和 Aliya 的 LLM 进行任何交互

上帝给 Aliya 的是"环境"，不是"剧本"。就像天气影响你的心情，但不决定你说的每一句话。

### 为什么不需要 Multi-Agent

现阶段不需要一个独立的 AI agent。原因：

1. **费用**：每次调用另一个 AI = 额外的 API 费用
2. **协调复杂度**：两个 AI 之间的矛盾处理是一个大工程
3. **上帝做的事情其实很简单**：选一个种子 + 决定触发不触发。随机函数 + 概率权重就够了
4. **后期可以升级**：等核心体验稳定了，再把上帝模块升级成 LLM 驱动的"叙事导演"，处理长线剧情（海盗入侵、大危机等）

### 上帝的决策记录

上帝每次做决定都要记录到数据库。这样：
- 程序关闭后重启，可以回溯离线期间发生了什么
- 可以调试和观察"命运"是否合理
- 后期可以基于历史数据调整概率权重

---

# 开发计划篇

---

## 整体架构（改造后）

```
现在的架构:
  User Input → ChatEngine → LLM → UI

目标架构:
  User Input ──┐
                ├──→ Prompt Builder ──→ LLM ──→ UI
  Life Sim ────┘        ↑                ↑
                   State Module      Database
                   (状态注入)        (消息持久化)
                        ↑
                   God Module
                   (日程 + 骰子)
```

### 新增文件

| 文件 | 职责 |
|------|------|
| `state.py` | 管理 Aliya 的所有动态状态（船时、活动、情绪、关系阶段） |
| `god.py` | 上帝模块（每日日程生成、随机事件骰子） |
| `seeds.json` | 情境种子库（30-50 个种子） |

### 修改的文件

| 文件 | 改动 |
|------|------|
| `config.py` | 增加时差常量、新状态的默认值 |
| `chat_engine.py` | 每次 API 调用时从 state 读取状态，动态注入 system prompt |
| `memory.py` | 数据库 schema 增加状态表、日程表、事件记录表 |
| `ui.py` | 离线消息展示、船时时钟修正 |
| `main.py` | 初始化 state、god 模块；启动时回溯 |

### 数据库新增表

```sql
-- Aliya 的当前状态
CREATE TABLE aliya_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- 每日日程（上帝模块生成）
CREATE TABLE daily_schedule (
    date TEXT PRIMARY KEY,          -- Aliya 的日期，如 "2026-04-16"
    wake_time TEXT,                  -- "10:30"
    sleep_time TEXT,                 -- "03:45"
    mood TEXT,                       -- "normal" / "low" / "high"
    work_seed_id TEXT,               -- 今天的工作内容种子
    is_staying_up INTEGER DEFAULT 0, -- 是否熬夜
    created_at TEXT DEFAULT (datetime('now'))
);

-- 随机事件记录
CREATE TABLE event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT DEFAULT (datetime('now')),
    seed_id TEXT,                    -- 触发的种子 ID
    event_type TEXT,                 -- "daily" / "work" / "emotional" / "danger"
    was_offline INTEGER DEFAULT 0,   -- 是否是回溯时补发的
    aliya_response TEXT              -- Aliya 对事件说了什么（用于调试）
);

-- 关系进度追踪
CREATE TABLE relationship (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- 只有一行
    phase INTEGER DEFAULT 1,                 -- 1-4
    first_interaction_date TEXT,             -- 第一次对话的日期
    total_conversation_turns INTEGER DEFAULT 0,
    active_days INTEGER DEFAULT 0,           -- 用户活跃天数
    last_active_date TEXT,
    phase_updated_at TEXT
);
```

---

## 分步开发计划

### 第一步：状态系统 + 动态 prompt 注入

**目标：** 建立 Aliya 有"状态"的基础。这一步做完就能立刻感受到回复风格的变化。

**改动：**

1. 新建 `state.py`：
```python
class AliyaState:
    """管理 Aliya 的所有动态状态。"""

    def get_ship_time(self) -> datetime:
        """返回 Aliya 的船时 = 系统时间 - 5小时。"""

    def get_activity(self) -> str:
        """根据当前船时和日程，返回 Aliya 在做什么。"""
        # 返回: "sleeping" / "waking_up" / "working" / "eating" /
        #       "idle" / "winding_down"

    def get_mood_today(self) -> str:
        """返回今天的语气基调。"""
        # 返回: "normal" / "low" / "high"

    def build_prompt_block(self) -> str:
        """生成要注入 system prompt 的状态文本块。"""
```

2. 修改 `chat_engine.py`：
   - `start_response()` 中，从 state 读取当前状态
   - 将状态块拼接到 system prompt 的固定部分之后、对话历史之前
   - 如果 Aliya 在睡觉，不调用 LLM，直接返回空

3. 修改 `config.py`：
   - 增加 `SHIP_TIME_OFFSET_HOURS = 5`

**风险点及处理：**
- **状态和 LLM 输出不一致**：在 prompt 里用角色口吻描述状态（"You're currently checking engine readings"），而不是系统指令（"You must reply briefly"）。让情境引导，不强制
- **跨天边界**：`get_ship_time()` 简单做减法，Python 的 `timedelta` 处理跨天自动正确
- **数据库缺失**：第一天运行时日程表为空，`state.py` 需要有合理的默认值（默认 idle，默认 normal mood）

**测试标准：**
- 启动应用，发送消息，确认 LLM 的 system prompt 中包含状态注入
- 修改状态为 "sleeping"，确认不触发 LLM 调用
- 确认船时显示正确（比系统时间晚 5 小时）

---

### 第二步：上帝模块 + 种子库

**目标：** Aliya 有了自己的"命运"——每天的日程和随机事件。这一步做完她就有了"不可预测性"。

**改动：**

1. 新建 `seeds.json`：
```json
[
    {
        "id": "daily_001",
        "type": "daily",
        "location": "engine_room",
        "mood_hint": "bored_curious",
        "context": "Routine maintenance check, found something unexpected",
        "weight": 10
    },
    {
        "id": "daily_002",
        "type": "daily",
        "location": "observation_deck",
        "mood_hint": "peaceful",
        "context": "Watching stars through the viewport, something caught attention",
        "weight": 8
    },
    ...
]
```

2. 新建 `god.py`：
```python
class God:
    """观察的上帝 — 决定 Aliya 的日常和命运。"""

    def generate_daily_schedule(self, date: str) -> dict:
        """生成某一天的日程。由 Aliya 凌晨调用。"""
        # 返回: {wake_time, sleep_time, mood, work_seed_id, is_staying_up}

    def roll_event_dice(self) -> dict | None:
        """投骰子决定是否触发随机事件。"""
        # 每 30-90 分钟调用一次
        # 返回: {seed_id, event_type} 或 None（什么都没发生）

    def ensure_schedule_exists(self, date: str):
        """检查某天的日程是否已生成，没有则生成。启动时回溯用。"""
```

3. 修改 `memory.py`：
   - 数据库 schema 增加 `daily_schedule`、`event_log` 表

4. 修改 `chat_engine.py`：
   - 如果有随机事件，将事件描述注入到 system prompt 的状态块之后
   - 注入格式：`[Something just happened]\n{事件描述}`

**风险点及处理：**
- **骰子触发时机**：用一个后台线程，每 5 分钟检查一次是否到了骰子时间。不在 UI 线程做随机等待
- **种子库质量**：初期 30 个种子够用。每个种子写得抽象一些（给方向），让 LLM 充实细节
- **"什么都没发生"的记录**：不记录（不需要数据库里有 70% 的"空"记录）。只记录实际触发的事件

**测试标准：**
- 确认每日日程生成正确（日程随日期变化，不是固定的）
- 确认骰子机制能触发事件
- 确认事件描述正确注入到 prompt 中
- 确认骰子有 70%+ 概率什么都没发生

---

### 第三步：关机回溯 + 离线消息

**目标：** 用户关闭再打开，能看到 Aliya 留的言。这是"人感"最关键的一步。

**改动：**

1. 修改 `main.py`：
   - 启动时调用回溯逻辑
   - 回溯完成后，如果有离线消息，展示在聊天区顶部

2. 在 `god.py` 中增加回溯方法：
```python
def catch_up(self, last_seen: datetime, now: datetime) -> list[dict]:
    """回溯从 last_seen 到 now 之间发生了什么。

    返回离线消息列表（最多 5 条），格式:
    [{"content": "...", "timestamp": "...", "type": "daily"|"event"|"missed"}]
    """
```

3. 修改 `ui.py`：
   - `main()` 中，回溯消息以 Aliya 气泡展示
   - 时间戳显示为消息实际"应该"出现的时间

**回溯逻辑的细节：**

```
catch_up(last_seen, now):
    messages = []
    hours_offline = (now - last_seen).total_hours() / 3600

    # 1. 生成离线期间的日程（确保日程表完整）
    for each day in offline period:
        god.ensure_schedule_exists(day)

    # 2. 模拟随机事件（抽样，不是每个骰子都算）
    num_event_rolls = hours_offline / 1  # 大约每小时一次
    for i in range(min(num_event_rolls, 20)):  # 最多检查 20 次
        event = god.roll_event_dice()
        if event:
            pending_events.append(event)

    # 3. 决定哪些事件值得写成离线消息
    #    规则：最多 3-5 条，间隔不要太密
    #    优先选择情绪类 > 工作类 > 日常类
    #    每条消息用 LLM 生成具体内容

    # 4. 如果离线时间跨过了 Aliya 的睡觉时间，
    #    可以加一条 "晚安" 或 "早安" 之类的

    return messages[:5]
```

**风险点及处理：**
- **回溯太久**：用户关了两周。不需要回溯两周的每一个事件。只抽样检查最近的事件，最多 5 条消息。两周前的日常小事不值得提
- **离线消息太多**：硬上限 5 条。宁可漏掉一些事件，也不要刷屏
- **时间戳可靠性**：如果用户改了系统时间，回溯可能产生不合理的结果。初期不管这个边界情况，架构上通过记录 last_seen 来防御大部分问题

**测试标准：**
- 关闭应用 1 小时后重启，确认有 0-2 条离线消息
- 关闭应用 1 天后重启，确认有 1-3 条离线消息
- 关闭应用 1 周后重启，确认最多 5 条消息
- 确认离线消息的时间戳合理
- 确认没有离线消息时也能正常运行

---

### 第四步：作息周期

**目标：** Aliya 的状态随时间自然变化——用户在不同时段看到不同的她。

**改动：**

1. 在 `state.py` 中完善 `get_activity()`：
   - 根据当前船时和今天的日程，判断 Aliya 在哪个阶段
   - 处理跨天边界（Aliya 凌晨 4 点睡觉，3:59 还醒着，4:01 睡了）
   - 处理"熬夜"情况（今天日程标记了 is_staying_up，睡觉时间推迟 1-2 小时）

2. 修改 `build_prompt_block()`：
   - 根据活动阶段注入不同的描述：
     - sleeping: "You're asleep. If Nolan messages you, you won't see it until you wake."
     - waking_up: "You just woke up. Still groggy. Short replies, not fully alert yet."
     - working: "You're in the middle of {work_description}. Hands busy, attention split."
     - eating: "You're having a meal. A quiet moment, relaxed."
     - idle: "You have free time. Nothing urgent to do."
     - winding_down: "Late night. Ship is quiet. You're a bit tired, a bit reflective."

3. 修改 `chat_engine.py`：
   - 如果 Aliya 在 sleeping，不调用 LLM。消息存库，不回复
   - 如果 Aliya 在 waking_up，降低 max_tokens 或在 prompt 里暗示短回复
   - 其他阶段正常调用

**风险点及处理：**
- **跨天边界**：`datetime` 运算自然处理。关键是在 `get_activity()` 里正确使用比较逻辑
- **状态切换过于生硬**：不要在 prompt 里写 "NOW YOU ARE WORKING"。用自然的描述，让 LLM 平滑过渡
- **用户在 Aliya 睡觉时发消息**：消息存库，不调用 API。Aliya 醒来后，下次被触发时有机会看到（不一定每次都提——她可能没注意，就像真人那样）

**测试标准：**
- 在 Aliya 不同的作息阶段发送消息，确认回复风格确实不同
- 确认睡觉时不调用 API
- 确认日程中的 work_description 正确注入

---

### 第五步：关系阶段系统

**目标：** Aliya 和用户的关系随时间渐进变化。

**改动：**

1. 修改 `memory.py`：
   - 数据库 schema 增加 `relationship` 表
   - 增加方法：`update_relationship()` 检查是否满足推进条件
   - 增加方法：`get_relationship_phase()` 返回当前阶段
   - 增加方法：`log_active_day()` 记录用户今天活跃

2. 在 `state.py` 中：
   - `build_prompt_block()` 包含关系阶段信息
   - 每个阶段对应不同的信任度描述

3. 修改 system prompt（`aliya_system_prompt.txt`）：
   - 把固定的信任描述改为占位符
   - 实际内容由 `state.py` 根据阶段动态生成

**阶段对应的 prompt 片段（示例）：**

阶段一：
> "You remember the hyacinth code. Someone from far away, far in the past, used it to reach you. But your memories are fragmented — the company's memory wipes weren't gentle. You're cautious. You don't share personal things easily."

阶段二：
> "You've been talking with this person for a while now. They seem... okay. You're starting to relax around them, share small things about your day. But you keep deeper feelings to yourself. You're not sure yet."

阶段三：
> "This person has become someone you look forward to hearing from. You trust them enough to share frustrations, small joys, random thoughts. Sometimes you catch yourself caring more than you expected. You don't say it out loud."

阶段四：
> "They matter to you. You don't say it often — you don't need to. It shows in the little things: you notice when they're quiet, you think about them during long shifts, you trust them with the parts of yourself you usually hide. But you're still you — you deflect, you tease, you change the subject when it gets too real."

**风险点及处理：**
- **LLM 不遵守阶段约束**：用角色口吻描述（"You keep deeper feelings to yourself"）而不是系统指令（"Don't express deep feelings"）。LLM 更容易遵守角色自述
- **阶段推进判断**：只在应用启动时和每天结束时检查。不在每次对话时都检查（浪费）
- **阶段不回退**：初期只做单向推进。吵架、冷战等复杂关系动态留给后期

**测试标准：**
- 确认阶段推进条件正确计算（天数 + 活跃天数 + 对话轮次）
- 确认阶段变化后 prompt 注入内容不同
- 确认阶段变化是渐进的（不是某天突然变了个人）

---

### 第六步：UI 改造（收尾）

**目标：** 让用户在界面上感受到所有这些变化。

**改动：**

1. 修正"Ship Time"显示：
   - 当前显示的是用户系统时间，应该改为 Aliya 的船时（系统时间 - 5 小时）
   - 格式：`Ship Time: 18:23` 或 `Ship Time: 03:47 (late night)`

2. 离线消息展示：
   - 应用启动时如果有离线消息，在聊天区顶部显示
   - 时间戳显示为消息实际"应该"出现的时间
   - 可以用一个淡入动画区分离线消息和实时消息

3. Aliya 睡觉时的界面提示：
   - 不要做显式的状态栏
   - 而是通过最后一条消息的时间和当前时间的差距来暗示
   - 如果用户在 Aliya 睡觉时发消息，输入框可以正常用，但发送后没有响应（像给朋友发微信，他睡着了）

**风险点及处理：**
- **消息顺序**：离线消息的时间戳在用户上次消息之前或之间。需要正确排序
- **时区显示**：`Ship Time` 只是一个简单的减法显示，不需要处理 DST 等复杂情况

---

## 架构纪律（必须遵守的规则）

### 1. 消息永远先存数据库，再决定是否调用 LLM

```
用户发消息 → 存入 messages 表 → 检查 Aliya 状态 → 决定是否调 API
```

这样即使不调用 API（Aliya 在睡觉），消息也不丢失。

### 2. 上帝模块的决策要持久化

每天的日程、骰子结果都写入数据库。程序关闭后重启可以回溯。可以调试"为什么今天 Aliya 这样"。

### 3. 不要在 UI 线程做任何随机决策

骰子、日程生成、状态切换都是后台线程或启动时批量处理。UI 线程只负责展示。

### 4. System prompt 的注入顺序

```
[固定部分] 性格、语言风格、世界设定
[动态部分] 当前状态、日程、关系阶段（由 state.py 生成）
[上下文部分] 随机事件（如果有，由 god.py 提供）
[对话历史] 最近 20 轮 + 摘要（由 memory.py 提供）
```

动态部分放在固定部分之后、对话历史之前。LLM 优先读到的是"她现在在干什么"。

### 5. 每一个状态变量都要有默认值

数据库里缺了某个字段时，不能崩。所有状态都应该有合理的 fallback。

### 6. 时差是 -5 小时，不是时区

```
ship_time = system_time - timedelta(hours=5)
```

不依赖系统时区设置。不管用户在哪个时区，Aliya 永远比用户晚 5 小时。

---

## 附录：不应该做的事

为了避免过度设计，明确列出不应该做的事：

1. **不要做好感度数值系统。** 不要让用户觉得在"刷好感"。
2. **不要做太多状态变量。** 不需要"饥饿值 73/100"这种精确数字。"有点饿了"就够了。
3. **不要做用户界面显示 Aliya 的状态。** 用户应该通过 Aliya 的话感受到她的状态，不是通过看 HUD。
4. **不要做复杂的事件树或分支剧情。** 事件是给 LLM 的素材，不是给用户的剧情。每个事件的展开方式应该由 LLM 根据上下文决定。
5. **不要试图控制 LLM 的输出格式。** 不要写"你应该回复 1-2 句"。给她情境，让她自己决定。
6. **不要让系统通知用户"Aliya 发来了新消息"。** 打开应用时看到就好。如果是重要的事，她会等你。
7. **现阶段不要做 Multi-Agent。** 上帝模块用随机函数实现。等核心体验稳定后再考虑升级。
8. **不要穷举所有事件。** 用情境种子 + LLM 生成。50 个种子 > 500 个穷举。
