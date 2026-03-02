import cv2
import mediapipe as mp
import numpy as np


# ==========================================
# 📐 核心算法：计算三个关节之间的夹角
# ==========================================
def calculate_angle(a, b, c):
    """
    计算 A(肩膀), B(手肘), C(手腕) 形成的夹角
    背后是向量夹角公式：θ = |arctan2(Cy-By, Cx-Bx) - arctan2(Ay-By, Ax-Bx)|
    """
    a = np.array(a)  # 肩膀坐标
    b = np.array(b)  # 手肘坐标 (顶点)
    c = np.array(c)  # 手腕坐标

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle


# ==========================================
# 👁️ 初始化 AI 视觉引擎 (MediaPipe)
# ==========================================
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# ⚠️ 老板，把这里的 'smash.mp4' 换成你真实的视频名字！
video_path = 'smash.mp4'
cap = cv2.VideoCapture(video_path)

# 获取原视频的宽度、高度和帧率，准备导出带分析数据的慢动作视频
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# 定义视频导出器 (Mac 上通常用 mp4v 编码)
out = cv2.VideoWriter('output_analyzed.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

print("🤖 鹰眼系统已启动，正在逐帧剥离人体骨骼数据...")

# 启用姿态识别大模型
with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # 视频读完了，退出循环

        # 1. 颜色转换：OpenCV 默认读入是 BGR，但 AI 模型吃的是 RGB，得换一下
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        # 2. 🧠 让 AI 脑子转起来：提取全身 33 个关键点的坐标！
        results = pose.process(image)

        # 3. 画图准备：把颜色换回来，准备在画面上画线写字
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # 4. 抽取关键数据并计算（假设你是右手持拍）
        try:
            landmarks = results.pose_landmarks.landmark

            # 获取 右肩(12), 右肘(14), 右腕(16) 的 x,y 坐标
            shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                        landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                     landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                     landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

            # 📐 调用咱们的数学公式算手肘夹角！
            angle = calculate_angle(shoulder, elbow, wrist)

            # 把算出来的角度，像科幻片一样实时钉在视频里的手肘位置！
            # (需要把 0~1 的比例坐标换算成视频里的真实像素坐标)
            cv2.putText(image, f"Elbow: {int(angle)} deg",
                        tuple(np.multiply(elbow, [width, height]).astype(int)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3, cv2.LINE_AA)

        except:
            pass  # 如果某几帧没拍到人（比如出画了），别报错，直接跳过

        # 5. 画出全身的赛博朋克骨骼线！
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                  mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                  mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))

        # 6. 把画好骨骼的这一帧，写入新视频，并实时显示
        out.write(image)
        cv2.imshow('AI Badminton Biomechanics', image)

        # 按 'q' 键可以强行提前退出
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

# 打扫战场，释放内存
cap.release()
out.release()
cv2.destroyAllWindows()
print("✅ 视频分析完毕！已生成生物力学分析文件：output_analyzed.mp4")