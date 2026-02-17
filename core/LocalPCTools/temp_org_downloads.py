# --------------------------------------------------------
# 文件名: organize_downloads.py
# 作用: 自动将文件分类移动到 Documents, Media, Archives 等文件夹
# --------------------------------------------------------
import os
import shutil
from pathlib import Path

# ================= 配置区域 =================
SOURCE_DIR = Path(os.path.expanduser("~/Downloads"))

# 分类规则
DESTINATIONS = {
    "00_Installers_(安装包)": [".dmg", ".pkg", ".iso", ".exe"],
    "01_Archives_(压缩包)": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "02_Documents_(文档)": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md", ".csv", ".json",
                            ".xml", ".xmind"],
    "03_Media_(媒体)": [".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov", ".avi", ".svg", ".webp"],
    "04_Code_(代码)": [".py", ".js", ".html", ".css", ".sh", ".java", ".sql", ".pem", ".pub", ".key"],
    "99_Others_(杂项)": []
}

# ⚠️⚠️⚠️ 安全开关 ⚠️⚠️⚠️
# True = 演习模式 (只打印日志，不移动文件，建议先跑这个！)
# False = 实战模式 (真的会移动文件)
DRY_RUN = False


def organize():
    if not SOURCE_DIR.exists():
        print(f"❌ 找不到文件夹: {SOURCE_DIR}")
        return

    print("=" * 60)
    print(f"🚀 整理目标: {SOURCE_DIR}")
    print(f"🔧 当前模式: {'👀 演习 (不修改文件)' if DRY_RUN else '⚡️ 实战 (移动文件)'}")
    print("=" * 60)

    count = 0

    for item in SOURCE_DIR.iterdir():
        # 跳过文件夹、隐藏文件、以及我们自己创建的分类文件夹
        if item.is_dir() or item.name.startswith("."):
            continue

        file_ext = item.suffix.lower()
        moved = False

        for folder_name, extensions in DESTINATIONS.items():
            # 逻辑：如果后缀匹配，或者归为杂项
            if file_ext in extensions or folder_name.startswith("99"):

                # 防止重复归类到杂项
                if folder_name.startswith("99") and moved:
                    continue

                target_folder = SOURCE_DIR / folder_name
                target_path = target_folder / item.name

                print(f"[{folder_name}] <--- {item.name}")

                if not DRY_RUN:
                    # 1. 创建文件夹
                    target_folder.mkdir(exist_ok=True)

                    # 2. 处理重名 (自动重命名 file_1.jpg)
                    if target_path.exists():
                        base = target_path.stem
                        ext = target_path.suffix
                        counter = 1
                        while target_path.exists():
                            target_path = target_folder / f"{base}_{counter}{ext}"
                            counter += 1

                    # 3. 移动
                    try:
                        shutil.move(str(item), str(target_path))
                    except Exception as e:
                        print(f"   ❌ 移动失败: {e}")

                moved = True
                count += 1
                break

    print("-" * 60)
    if DRY_RUN:
        print(f"👀 扫描结束，预计移动 {count} 个文件。")
        print("💡 确认没问题后，请将代码里的 'DRY_RUN = True' 改为 'False' 再运行一次。")
    else:
        print(f"✅ 整理完成！共移动 {count} 个文件。")


if __name__ == "__main__":
    organize()