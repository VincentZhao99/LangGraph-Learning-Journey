import streamlit as st
import cv2
import numpy as np
import os
import tempfile
import warnings
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

warnings.filterwarnings("ignore")
load_dotenv()


# ==========================================
# 📐 核心数学公式
# ==========================================
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0: angle = 360 - angle
    return angle


# ==========================================
# 👁️ 多态视觉引擎 (带时间轴裁剪功能)
# ==========================================
def process_video(input_path, output_path, action_type, start_sec, end_sec):
    import mediapipe as mp
    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose

    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or np.isnan(fps): fps = 30

    # 计算需要截取的起始帧和结束帧
    start_frame = int(start_sec * fps)
    end_frame = int(end_sec * fps)

    fourcc = cv2.VideoWriter_fourcc(*'vp80')
    out = cv2.VideoWriter(output_path, fourcc, int(fps), (width, height))

    # 用于记录极限数据的变量
    metrics = {"min_angle": 360.0, "max_angle": 0.0}

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        current_frame = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            # 💡 核心剪辑逻辑：不到起始时间就跳过，超过结束时间就直接罢工（极速省时间）！
            if current_frame < start_frame:
                current_frame += 1
                continue
            if current_frame > end_frame:
                break

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark

                # 💡 动态骨骼抓取：根据动作类型，抓取不同的关节！
                if action_type == "高远球/杀球 (测上肢发力)":
                    # 抓取右臂：肩(12), 肘(14), 腕(16)
                    p1 = [landmarks[12].x, landmarks[12].y]
                    p2 = [landmarks[14].x, landmarks[14].y]
                    p3 = [landmarks[16].x, landmarks[16].y]
                    label = "Elbow"
                else:
                    # 抓取下肢弓箭步 (网前挑球)：右髋(24), 右膝(26), 右踝(28)
                    p1 = [landmarks[24].x, landmarks[24].y]
                    p2 = [landmarks[26].x, landmarks[26].y]
                    p3 = [landmarks[28].x, landmarks[28].y]
                    label = "Knee"

                angle = calculate_angle(p1, p2, p3)

                # 记录这3秒内的极值
                if angle < metrics["min_angle"]: metrics["min_angle"] = angle
                if angle > metrics["max_angle"]: metrics["max_angle"] = angle

                # 实时渲染角度
                cv2.putText(image, f"{label}: {int(angle)}",
                            tuple(np.multiply(p2, [width, height]).astype(int)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3, cv2.LINE_AA)

                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            except:
                pass

            out.write(image)
            current_frame += 1

    cap.release()
    out.release()
    return metrics


# ==========================================
# 🧠 动态大模型教练 (根据动作切换评价体系)
# ==========================================
def generate_coach_report(action_type, metrics):
    model = ChatOpenAI(
        model='deepseek-chat',
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
    )

    # 💡 动态提示词：不同动作，不同的考核标准！
    if action_type == "高远球/杀球 (测上肢发力)":
        prompt = f"""你是一位羽毛球金牌私教。学员刚才进行了【高远球/杀球】训练。
        CV底层提取的上肢发力数据如下：
        - 引拍最深处手肘夹角：{int(metrics['min_angle'])}度（优秀标准：45-70度）
        - 击球瞬间手肘最大夹角：{int(metrics['max_angle'])}度（优秀标准：160-180度）
        请写一份专业、毒舌带关怀的诊断报告，并给出改善引拍的3个训练建议！"""
    else:
        prompt = f"""你是一位羽毛球金牌私教。学员刚才进行了【网前挑球】训练。
        挑球的核心在于最后一步的弓箭步是否扎实。CV底层提取的下肢弓箭步数据如下：
        - 跨步下压最深处的膝盖夹角：{int(metrics['min_angle'])}度（优秀标准：90-110度，太小伤膝盖且起不来，太大没刹住车）
        请写一份专业、毒舌带关怀的诊断报告，指出他的步法和重心问题，并给出改善网前弓箭步的3个训练建议！"""

    response = model.invoke([HumanMessage(content=prompt)])
    return response.content


# ==========================================
# 🖥️ Streamlit 炫酷前端 (增加剪辑台与多态选择)
# ==========================================
st.set_page_config(page_title="Pro 鹰眼私教舱", page_icon="🏸", layout="wide")
st.title("🏸 Pro 鹰眼生物力学私教系统 (多态诊断版)")

# 💡 业务选择下拉框
action_selection = st.selectbox("🎯 请选择您要分析的技术动作：", ["高远球/杀球 (测上肢发力)", "网前挑球 (测下肢弓箭步)"])

uploaded_file = st.file_uploader("📂 请上传原始视频 (支持长视频)", type=['mp4', 'mov'])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    input_video_path = tfile.name
    output_video_path = input_video_path.replace('.mp4', '_analyzed.webm')

    # 💡 极速读取视频总时长，渲染剪辑滑块
    cap = cv2.VideoCapture(input_video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = total_frames / fps if fps > 0 else 10.0
    cap.release()

    st.markdown("### ✂️ 视频切片工作台")
    st.info(f"原视频总时长：**{duration:.1f} 秒**。为了防止干扰数据，请截取【包含完整动作前后的 2-3 秒精华片段】！")

    # 强大的双头滑块，精确到 0.1 秒！
    start_time, end_time = st.slider(
        "滑动选取分析区间 (秒)",
        0.0, float(duration),
        (0.0, min(3.0, float(duration))),
        step=0.1
    )

    if st.button("🚀 开始精准鹰眼诊断", type="primary"):
        col1, col2 = st.columns([1, 1])

        with col1:
            with st.status(f"👁️ 正在截取 {start_time}s - {end_time}s，分析【{action_selection}】...",
                           expanded=True) as status_cv:
                # 把时间参数和动作类型传给视觉引擎！
                metrics = process_video(input_video_path, output_video_path, action_selection, start_time, end_time)
                status_cv.update(label="✅ 骨骼极值解析完毕！", state="complete", expanded=False)

            st.success(
                f"📊 提取成功：最小夹角 **{int(metrics['min_angle'])}°** | 最大夹角 **{int(metrics['max_angle'])}°**")
            st.video(output_video_path)

        with col2:
            with st.status("🧠 金牌教练正在根据最新数据和动作类型撰写报告...", expanded=True) as status_llm:
                report = generate_coach_report(action_selection, metrics)
                status_llm.update(label="✅ 诊断报告生成完毕！", state="complete", expanded=False)

            st.markdown(report)
            st.balloons()