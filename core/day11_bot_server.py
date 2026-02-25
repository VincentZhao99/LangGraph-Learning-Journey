# 文件路径：day11_bot_server.py
from fastapi import FastAPI, Request
import requests
import uvicorn

# 引入我们 Day 9 或者 Day 10 写好的图流转逻辑 (假设你把组装图的逻辑封装成了函数)
# from day9_app import app as agent_app, config

app = FastAPI(title="AI Agent 机器人网关")

# 【大白话】：这是企业微信或钉钉机器人的 Webhook 地址（你需要明天去群里建一个机器人获取这个地址）
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的机器人的KEY"


def send_to_group(text: str):
    """【大白话】：把咱们 Agent 吐出来的最终结果，通过接口发到微信/钉钉群里"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "msgtype": "text",
        "text": {
            "content": text
        }
    }
    # 就像你用邮局寄信一样，把 payload 寄给腾讯/阿里的服务器
    requests.post(WEBHOOK_URL, headers=headers, json=payload)


@app.post("/chat")
async def receive_message(request: Request):
    """
    【大白话】：这里是咱们服务器的大门。
    如果别人（比如钉钉）给我们的公网地址发了 POST 请求，就会触发这个函数。
    """
    # 1. 拆开别人发来的包裹，拿出里面的文本内容
    data = await request.json()
    user_query = data.get("text", {}).get("content", "").strip()

    if not user_query:
        return {"status": "empty query"}

    # 2. 召唤咱们的 LangGraph Agent 开始干活！
    print(f"收到群消息: {user_query}，正在呼叫 Agent 大脑...")

    # 【注】：这里用伪代码代替，明天咱们把 Day9/10 的代码正式嵌进来
    # inputs = {"messages": [("user", user_query)]}
    # response_content = ""
    # for event in agent_app.stream(inputs, config):
    #     if "agent" in event:
    #         response_content = event["agent"]["messages"][-1].content

    # 假设这是 Agent 憋出来的大招
    agent_reply = f"🤖 Agent 收到！你刚才说的是：{user_query}。（图的流转结果将在这里拼接）"

    # 3. 把 Agent 的大招发回群里
    send_to_group(agent_reply)

    return {"status": "success", "msg": "已回复"}


if __name__ == "__main__":
    # 【大白话】：把咱们的服务器在本地 8000 端口启动起来！
    uvicorn.run(app, host="0.0.0.0", port=8000)