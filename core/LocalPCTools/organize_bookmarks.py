import json
import os
import time
from pathlib import Path

# ================= 配置区域 =================
# Chrome 书签路径 (Mac 标准路径)
CHROME_BOOKMARK_PATH = Path(os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Bookmarks"))
# 输出文件路径 (生成在桌面)
OUTPUT_HTML = Path(os.path.expanduser("~/Desktop/Cleaned_Bookmarks.html"))

# 🧹 分类规则 (关键词匹配: 只要标题或URL包含这些词，就扔进对应的文件夹)
# 这里的关键词是根据你刚才的截图定制的
RULES = {
    "📂 01_Projects_(进行中)": [
        "jira", "confluence", "trello", "gitlab", "github",
        "chinacrm", "sanofi", "project", "ticket", "case"
    ],
    "📂 02_Areas_(生活_职业)": [
        "finance", "stock", "bank", "invest", "雪球", "理财", "银行",  # Finance
        "career", "resume", "job", "linkedin", "招聘", "转行", "老师",  # Career
        "badminton", "sport", "health", "羽毛球", "装修", "小米", "家居",  # Life
        "shopping", "amazon", "taobao", "jd.com", "price"
    ],
    "📂 03_Resources_(第二大脑)": [
        "aws", "cloud", "docker", "kubernetes", "linux", "ubuntu",  # DevOps
        "python", "java", "code", "programming", "tutorial", "guide",  # Code
        "math", "calculus", "probability", "statistics", "可汗", "高数",  # Math
        "salesforce", "veeva", "crm", "doc", "documentation", "manual",  # Work Docs
        "course", "bilibili", "youtube", "learning", "study", "笔记"  # Learning
    ],
    "⚡️ Toolbox_(工具箱)": [
        "tool", "converter", "calculator", "translator", "gpt", "ai", "gemini",
        "compare", "diff", "counter", "json", "format", "query"
    ]
}

# 兜底文件夹 (匹配不到的放这里)
UNSORTED_FOLDER = "99_Unsorted_(待整理)"


def load_bookmarks(path):
    """读取 Chrome 的 JSON 书签文件"""
    if not path.exists():
        print(f"❌ 找不到 Chrome 书签文件: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return None


def extract_urls(node, urls_list):
    """递归提取所有书签 URL"""
    if isinstance(node, dict):
        if "type" in node and node["type"] == "url":
            urls_list.append({
                "name": node["name"],
                "url": node["url"],
                "add_date": node.get("date_added", "0")
            })
        if "children" in node:
            for child in node["children"]:
                extract_urls(child, urls_list)
    elif isinstance(node, list):
        for child in node:
            extract_urls(child, urls_list)


def categorize_bookmarks(all_bookmarks):
    """核心逻辑: 按规则分类"""
    organized = {key: [] for key in RULES.keys()}
    organized[UNSORTED_FOLDER] = []

    count = 0
    for item in all_bookmarks:
        title = item["name"].lower()
        url = item["url"].lower()
        matched = False

        for folder, keywords in RULES.items():
            for kw in keywords:
                if kw in title or kw in url:
                    organized[folder].append(item)
                    matched = True
                    break
            if matched:
                break

        if not matched:
            organized[UNSORTED_FOLDER].append(item)
        count += 1

    return organized, count


def generate_netscape_html(organized_data):
    """生成 Chrome 可识别的 HTML 导入文件"""
    html = ['<!DOCTYPE NETSCAPE-Bookmark-file-1>',
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
            '<TITLE>Bookmarks</TITLE>',
            '<H1>Bookmarks</H1>',
            '<DL><p>']

    for folder_name, items in organized_data.items():
        if not items: continue  # 跳过空文件夹

        html.append(f'<DT><H3>{folder_name}</H3>')
        html.append('<DL><p>')

        for item in items:
            name = item["name"].replace('"', '&quot;')
            url = item["url"]
            html.append(f'<DT><A HREF="{url}">{name}</A>')

        html.append('</DL><p>')

    html.append('</DL><p>')
    return "\n".join(html)


def main():
    print(f"🚀 开始读取 Chrome 书签...")
    data = load_bookmarks(CHROME_BOOKMARK_PATH)

    if not data:
        return

    # 1. 提取 (把原本乱七八糟的树形结构打平)
    all_bookmarks = []
    # Chrome 书签主要在 'bookmark_bar' 和 'other' 下
    roots = data.get("roots", {})
    extract_urls(roots.get("bookmark_bar", {}), all_bookmarks)
    extract_urls(roots.get("other", {}), all_bookmarks)
    extract_urls(roots.get("synced", {}), all_bookmarks)

    print(f"📦 共扫描到 {len(all_bookmarks)} 个书签")

    # 2. 清洗 (按 PARA 规则分类)
    organized_data, total = categorize_bookmarks(all_bookmarks)

    # 3. 生成 (写入 HTML)
    html_content = generate_netscape_html(organized_data)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print("-" * 60)
    print(f"✅ 整理完成！")
    print(f"📂 生成文件: {OUTPUT_HTML}")
    print("-" * 60)
    print("👉 下一步操作指南:")
    print("1. 打开 Chrome -> 书签管理器 (Option+Cmd+B)")
    print("2. 点击右上角三个点 -> '导入书签'")
    print("3. 选择桌面上的 'Cleaned_Bookmarks.html'")
    print("4. 你的书签栏会出现一个 'Imported' 文件夹，里面就是整理好的 PARA 结构！")


if __name__ == "__main__":
    main()