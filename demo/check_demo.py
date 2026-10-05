# -*- coding: utf-8 -*-
"""功能演示站自检：确认数据注入 + 复刻页面检索打分逻辑验证路由。
数据源直接读取 seed/knowledge-base（与页面内联数据同源，可复现）。
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEMO = ROOT / "demo" / "企业知识助手-功能演示.html"
KB_ROOT = ROOT / "seed" / "knowledge-base"

CATS = {
    "01-product-manual": "产品说明书",
    "02-technical-docs": "技术文档",
    "03-it-ops-sop": "IT 运维 SOP",
    "04-after-sales": "售后流程",
    "05-faq": "FAQ",
}
KB = []
for folder, label in CATS.items():
    for f in sorted((KB_ROOT / folder).glob("*.md")):
        lines = f.read_text(encoding="utf-8").splitlines()
        title, body = "", []
        for ln in lines:
            if ln.startswith("# "):
                title = ln[2:].strip()
            else:
                body.append(ln)
        KB.append({"title": title, "category": label, "content": "\n".join(body).strip()})

html = DEMO.read_text(encoding="utf-8")
if "/*__KB_DATA__*/" in html:
    data = json.dumps(KB, ensure_ascii=False, indent=1)
    html = html.replace("const KB = /*__KB_DATA__*/[];", "const KB = " + data + ";")
    DEMO.write_text(html, encoding="utf-8")
    print("注入完成:", len(html), "字符")
else:
    print("注入已在先前完成（占位符不存在）")


def segs(doc):
    out = []
    for p in re.split(r"\n\n+", doc["content"]):
        t = re.sub(r"\|", " ", p).strip()
        if len(t) >= 8:
            out.append((doc["title"], doc["category"], t))
    return out


ALL = [s for d in KB for s in segs(d)]


STOP = {"怎么", "如何", "怎样", "为什么", "什么", "请问", "吗", "呢", "哪里", "多少",
        "时候", "可以", "能否", "怎么办", "那个", "这个", "的话"}


def grams(t):
    t = re.sub(r"[，。、；：？！,.;:?!\"“”‘’()\[\]{}|`*#\-]", " ", t.lower())
    g = set()
    for m in re.findall(r"[\u4e00-\u9fff]+|[a-z0-9_.]+", t):
        if re.search(r"[\u4e00-\u9fff]", m):
            for i in range(len(m) - 1):
                g.add(m[i:i + 2])
            if len(m) == 2:
                g.add(m)
        else:
            g.add(m)
    g.difference_update(STOP)
    return g


def search(q):
    qg = grams(q)
    res = []
    for title, cat, text in ALL:
        sg = grams(text)
        hit = sum(1 for g in qg if g in sg)
        sc = hit / len(qg) if qg else 0
        if text.startswith("##"):
            sc += 0.1
        sc = min(sc, 0.95)
        if sc > 0:
            res.append((title, cat, round(sc, 2)))
    res.sort(key=lambda x: -x[2])
    return res[:3]


tests = [
    "VPN 连接超时怎么办？",
    "电脑蓝屏 MEMORY_MANAGEMENT 怎么处理？",
    "邮箱发不出邮件怎么办？",
    "网关固件升级失败如何处理？",
    "YF-Suite 支持哪些浏览器？",
    "今天天气怎么样？",
]
print("\n===== 路由功能自检（阈值 0.30）=====")
for q in tests:
    r = search(q)
    hit = bool(r) and r[0][2] >= 0.30
    top = r[0] if r else None
    print(("命中" if hit else "兜底"), "|", q, "=>", top)
