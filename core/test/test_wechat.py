import requests

# ⚠️ 把这里换成你刚刚复制的那串真实的 Webhook URL
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的真实KEY"


def send_test_msg():
    # 企微机器人固定要求的包裹格式
    payload = {
        "msgtype": "markdown",  # 支持 markdown 格式，排版更好看
        "markdown": {
            "content": "🚨 **老板好！**\n> 我是你的全能 Agent，我已经成功潜入企微群啦！随时准备发布文章！"
        }
    }

    print("正在呼叫企微服务器...")
    # 把包裹寄出去
    response = requests.post(WEBHOOK_URL, json=payload)
    print("企微服务器返回结果:", response.text)


if __name__ == "__main__":
    send_test_msg()