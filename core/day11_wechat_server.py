from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse
from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
import uvicorn

app = FastAPI(title="企微双向通信网关")

# ==========================================
# ⚠️ 填入你刚才在企微后台白嫖到的参数！
# ==========================================
TOKEN = "填你的Token"
ENCODING_AES_KEY = "填你的EncodingAESKey"
CORP_ID = "填你的企业ID(CorpID)"

# 初始化企微的“密码机”
crypto = WeChatCrypto(TOKEN, ENCODING_AES_KEY, CORP_ID)

@app.get("/wechat")
async def verify_url(
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...)
):
    """
    【大白话】：这里是应对企微第一次“握手”校验的专属通道。
    当你点“保存”时，企微会往这里扔一串加密乱码 (echostr)。
    如果我们解密成功并原样还给它，它就承认这个服务器是我们的。
    """
    print(f"👀 收到企微校验请求！时间戳: {timestamp}")
    try:
        # 把乱码扔进密码机解密
        decrypted_echostr = crypto.decrypt_message(
            msg_signature,
            timestamp,
            nonce,
            echostr
        )
        print("✅ 解密成功！准备放行！")
        # ⚠️ 企微极其死板，必须且只能返回纯文本的解密字符串
        return PlainTextResponse(content=decrypted_echostr)
    except InvalidSignatureException:
        print("❌ 签名校验失败！可能是参数填错了。")
        return PlainTextResponse(content="校验失败", status_code=403)

if __name__ == "__main__":
    print("🚀 AI 网关服务器已启动！")
    print("请去企微后台点击【保存】...")
    # 启动在 8000 端口，刚好对接你的 cpolar
    uvicorn.run(app, host="0.0.0.0", port=8000)