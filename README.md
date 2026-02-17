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
