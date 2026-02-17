import os
import shutil
from pathlib import Path
import datetime

# ================= 配置 =================
DOWNLOAD_DIR = Path(os.path.expanduser("~/Downloads"))
APP_DIR = Path("/Applications")

# 定义颜色 (让输出更好看，像黑客帝国一样)
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'


def get_file_size(path):
    # 计算文件夹大小 (MB)
    total = 0
    if path.is_file():
        total = path.stat().st_size
    else:
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    return total / (1024 * 1024)


def scan_applications():
    print(f"{BOLD}🚀 开始扫描下载文件夹中的应用程序 (.app)...{RESET}")
    print("-" * 60)

    found_apps = []
    installers = []

    # 1. 遍历下载文件夹
    for item in DOWNLOAD_DIR.iterdir():
        # 忽略隐藏文件
        if item.name.startswith("."):
            continue

        # 识别 .app (这就是你直接运行的软件)
        if item.suffix == ".app":
            found_apps.append(item)

        # 识别安装包 (dmg/pkg/iso - 这些通常是安装完可以删的)
        elif item.suffix in ['.dmg', '.pkg', '.iso']:
            installers.append(item)

    # 2. 分析发现的 App
    if not found_apps:
        print(f"{GREEN}✅ 太棒了！你的下载文件夹里没有遗留的应用程序。{RESET}")
    else:
        print(f"{YELLOW}⚠️  发现 {len(found_apps)} 个应用程序“流浪”在下载文件夹里：{RESET}\n")

        print(f"{'应用程序名':<30} | {'状态':<15} | {'建议操作'}")
        print("-" * 70)

        for app in found_apps:
            app_name = app.name
            system_app_path = APP_DIR / app_name

            status = ""
            action = ""
            color = ""

            if system_app_path.exists():
                # 系统里已经有了 (可能是重复下载，或者旧版本)
                status = "系统已存在"
                action = "对比版本后删除副本"
                color = YELLOW
            else:
                # 系统里没有 (这是真正的黑户！)
                status = "❌ 未安装"
                action = f"🔥 必须移动到 {APP_DIR}"
                color = RED

            print(f"{color}{app_name:<30} | {status:<15} | {action}{RESET}")

    print("-" * 60)

    # 3. 分析安装包
    if installers:
        print(f"\n📦 另外发现 {len(installers)} 个安装包文件 (dmg/pkg)：")
        print(f"   (如果软件已安装，这些通常可以安全删除)")
        for installer in installers[:5]:  # 只显示前5个
            print(f"   - {installer.name}")
        if len(installers) > 5:
            print(f"   ... 以及其他 {len(installers) - 5} 个")

    print("\n" + "=" * 60)
    print(f"{BOLD}🤖 建议操作步骤：{RESET}")
    if found_apps:
        print("1. 对于标红的 '未安装' App：请手动拖拽到 '应用程序' 文件夹。")
        print("2. 对于标黄的 '系统已存在' App：检查是否是新版本，如果不是，直接删除下载文件夹里的副本。")
    print("3. 确认软件能运行后，运行之前的清理脚本删除所有 .dmg 和 .zip。")


if __name__ == "__main__":
    scan_applications()