🤖 LangGraph 智能体进化之旅 (Learning Journey)本项目记录了我从零开始，基于 LangGraph 和 DeepSeek 构建工业级智能体（Agent）的学习过程。

📈 进化路径
🟢 Phase 1: 基础建设 (Day 1 - Day 3)
  核心目标：理解 LLM 的“大脑”与“手”的连接。
  关键成就：
    完成环境搭建，集成 DeepSeek 模型。
    定义第一个本地工具：multiply（高精度乘法）。
    掌握 Tool 装饰器及其类型提示（Type Hinting）的重要性。
🟡 Phase 2: 架构初成 (Day 4)
  核心目标：构建第一个闭环智能体。
  关键成就：
    使用 create_react_agent 搭建 ReAct (Reasoning and Acting) 架构。
    引入 MemorySaver 持久化记忆，实现多轮对话状态跟踪。
    实现了 Agent 自动判断何时调用工具、何时回答用户。
  🟠 Phase 3: 人格注入 (Day 5)
    核心目标：控制 Agent 的行为逻辑与语气。
    关键成就：
      注入 System Prompt (通过 messages_modifier)。
      塑造“专业行政助理”人格：不仅给出计算结果，还会进行办公场景的业务解释。
      加入时间感知：根据当前系统时间提供差异化的温馨提醒（如深夜提醒休息）。
    🔴 Phase 4: 安全与交互 (Day 6)
    核心目标：实现人机协作 (Human-in-the-loop)。
    关键成就：中断机制：设置 interrupt_before=["tools"]，在执行高风险操作前强制暂停。
    动态审批：支持 y (批准) / n (拒绝) 交互。
    状态重定向：解决拒绝后的状态冲突，利用 ToolMessage 伪造技术引导 Agent 重新规划任务路径。
    持续对话：构建 while True 嵌套循环，支持动态输入指令及多轮任务流转。
🛠️ 工具箱定义 (Tools)
  工具名功能描述
    multiply接收 num1 和 num2，返回高精度的乘法计算结果。
    get_current_time获取本地系统当前日期和时间，用于时间感知逻辑。
  
🚀 快速启动环境准备:
    Bashpip install langgraph langchain-openai python-dotenv
  配置秘钥:
    在根目录创建 .env 文件，填入：
      PlaintextDEEPSEEK_API_KEY=你的秘钥
      DEEPSEEK_BASE_URL=https://api.deepseek.com
    运行:Bash
      python core/main.py
📅 下一步计划 (Next)Day 7: 集成 Tavily Search，开启联网搜索能力，打破知识库的时空限制。

阶段一：破冰与连通（调包侠阶段）
核心技能：学会了配置环境变量（.env），拿到了 DeepSeek 的 API Key。

里程碑：你成功让 Python 脚本和云端的大模型说上了话。这个时候的 AI 只是一个“懂很多知识，但不联网、记不住你是谁”的单机版大脑。

阶段二：装配武器库（全能单体 Agent）
核心技能：引入 LangGraph 和 LangChain 的工具调用（Tool Calling）机制。

里程碑：

装上眼睛：接入 Tavily 搜索，AI 学会了自己上网查最新新闻。

装上海马体：接入 SQLite 数据库（SqliteSaver），AI 拥有了永久记忆，再刷新也不会失忆。

装上私有知识：手撕 FAISS 向量数据库和文本切割，实现了 RAG（检索增强生成），AI 可以阅读并回答你专属 PDF 里的内容了。

阶段三：产品化与前端（全栈开发）
核心技能：掌握 Streamlit 数据流框架。

里程碑：脱离了简陋的黑色终端终端，你用几十行纯 Python 代码，徒手捏出了一个带有交互气泡、加载动画（Spinner）和侧边栏的现代化 Web 产品。

阶段四：工业级架构（多智能体 Multi-Agent）
核心技能：掌握图论（Graph）在 AI 里的应用，理解节点（Node）、边（Edge）和条件路由（Conditional Edge）。

里程碑：你不再是一个只写死代码的程序员，而是成了一家“AI 公司的老板”。你成功让“研究员”、“写手”和“主编”三个独立的 AI 角色在你的代码里互相打配合，甚至实现了复杂的“打回重写”循环逻辑。

=====================================

目前硅谷最顶级的 Agent 架构，无非就是 “记忆（Memory） + 外部工具（Tools/RAG） + 流程编排（LangGraph） + 人机协同（HITL）” 这四大基石

🧠 第一层：大脑与对话底座 (Day 1 - Day 3)

你掌握了如何调用 DeepSeek API，懂得了 SystemMessage (设定人设) 和 HumanMessage (下达指令) 的区别。

📖 第二层：记忆与外部眼睛 (Day 4 - Day 8)

短期/长期记忆： 你搞懂了 Streamlit 的 session_state（刷新即焚）和 SqliteSaver（数据库永久记忆）。

RAG (检索增强生成)： 你学会了把私有文档切块、向量化，让 AI 能够回答知识库里的问题，拒绝幻觉。

全网搜索： 接入了 Tavily 搜索工具，让大模型连上了 2026 年的互联网。

🦾 第三层：物理双手 (Day 11 - Day 12)

Code Interpreter (代码解释器)： 这是最硬核的一战。你用 langchain-experimental 让 AI 具备了写 Python、执行 Python、处理复杂 Excel 表格、甚至画出 4 宫格数据报表的能力。AI 从此拥有了改变物理世界（文件系统）的力量！

🏭 第四层：工业级流水线编排 (Day 9 - Day 14)

LangGraph 多智能体协同： 你彻底抛弃了“聊天框”，学会了像画流程图一样（StateGraph），把【研究员】、【撰稿人】、【主编】和【发报房】拼装在一起。

动态路由与条件判断： 实现了“主编打回 -> 写手重写”的死循环逻辑。

Agent-in-Agent 架构： 让研究员节点本身就是一个自带循环的代码机器。

Human-in-the-Loop (老板审批)： 实现了人机协同的完美闭环。