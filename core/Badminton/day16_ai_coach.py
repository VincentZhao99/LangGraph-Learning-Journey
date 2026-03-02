import cv2
import numpy as np
import os
import warnings
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

warnings.filterwarnings("ignore")
load_dotenv()


# ==========================================
# 📐 核心数学公式 (保持不变)
# ==========================================
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0: angle = 360 - angle
    return angle


# ==========================================
# 👁️ 魔法一：将视觉代码封装为 AI 的“专属工具”
# ==========================================
@tool
def analyze_swing_biomechanics(video_path: str) -> str:
    """
    极其强大的视觉分析工具！
    输入羽毛球视频的文件路径，该工具将自动提取人体骨骼，并返回引拍最小角度和击球最大角度。
    """
    import mediapipe.python.solutions.drawing_utils as mp_drawing
    import mediapipe.python.solutions.pose as mp_pose

    print(f"\n🎥 [系统底层] 正在启动鹰眼视觉引擎，解析视频: {video_path} ...")
    cap = cv2.VideoCapture(video_path)

    # 💡 核心抓取：初始化两个极值变量
    min_angle = 360.0  # 记录引拍最深处（手肘弯曲最小）
    max_angle = 0.0  # 记录击球最高点（手肘伸展最大）

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            try:
                landmarks = results.pose_landmarks.landmark
                # 获取右臂坐标 (假设是右手持拍)
                shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                            landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                         landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                         landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

                angle = calculate_angle(shoulder, elbow, wrist)

                # 💡 抓取极限数据！
                if angle < min_angle: min_angle = angle
                if angle > max_angle: max_angle = angle
            except:
                pass

    cap.release()
    print("✅ [系统底层] 视觉解析完毕！正在将生物力学数据反馈给大模型大脑...")

    # 💡 把死板的数字，翻译成大模型能听懂的“数据报告”返回给它
    return f"视频分析完毕！该学员的引拍最深处手肘夹角为 {int(min_angle)} 度，击球瞬间手肘最大夹角为 {int(max_angle)} 度。"


# ==========================================
# 🧠 魔法二：组装金牌 AI 教练大脑
# ==========================================
model = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
)

# 给教练植入专业的羽毛球知识库
SYSTEM_PROMPT = """你是一位拥有 20 年执教经验的世界级羽毛球金牌私教。
你的任务是根据 analyze_swing_biomechanics 工具传回的生物力学数据，为学员写一份极其专业的诊断报告。

【专业评判标准】：
1. 优秀的引拍：手肘夹角应该在 45度 到 70度 之间，像拉满的弓。如果大于 80度，说明引拍不充分，无法借力。
2. 优秀的击球：击球瞬间手臂应该几乎伸直，手肘夹角应在 160度 到 180度 之间。如果小于 150度，说明击球点太低，或者发力缩手缩脚。

【语气要求】：专业、毒舌但带有关怀，多用 emoji。必须结合工具返回的具体数字进行分析！给出具体的改进训练建议！
"""

# 把长了眼睛的工具发给教练
ai_coach = create_react_agent(model, tools=[analyze_swing_biomechanics], prompt=SYSTEM_PROMPT)

print("=" * 50)
print("🏸 你的专属金牌 AI 视觉私教已上线！")
print("=" * 50)

# ==========================================
# 🚀 魔法三：下达终极指令
# ==========================================
# ⚠️ 注意：这里直接用了你截图里的视频名字！
user_input = "教练，请帮我分析一下 `天一高远.mp4` 这段视频里的挥拍动作，给我一份诊断报告！"
print(f"👤 你的指令: {user_input}")

inputs = {"messages": [HumanMessage(content=user_input)]}

# 监听教练的思考和发话过程
for event in ai_coach.stream(inputs, stream_mode="updates"):
    for node_name, state_update in event.items():
        if type(state_update) is not dict or "messages" not in state_update:
            continue
        msg = state_update["messages"][-1].content

        if node_name == "agent" and state_update["messages"][-1].tool_calls:
            print("\n🧠 教练思考中：发现需要分析视频，正在呼叫视觉底层引擎...")
        elif node_name == "tools":
            print(f"\n📊 视觉引擎反馈数据: {msg}")
        elif node_name == "agent" and not state_update["messages"][-1].tool_calls:
            print(f"\n🏆 【AI 教练的终极诊断报告】:\n\n{msg}")