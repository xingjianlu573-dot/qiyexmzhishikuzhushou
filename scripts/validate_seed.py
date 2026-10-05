# -*- coding: utf-8 -*-
"""校验种子知识库数据（seed/knowledge-base/）。

校验项：
1. 每个分类目录至少 2 篇文档，文档为非空 UTF-8 文本
2. 每篇文档含一级标题（# 开头）与正文字数阈值（>= 200 字，保证可检索/可分块）
3. 文档编码无异常（能正常按 utf-8 解码）
4. 覆盖 5 大业务分类（产品说明书/技术文档/IT运维SOP/售后流程/FAQ）
5. 输出每个分类的文档清单与规模，供 README 引用
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "seed" / "knowledge-base"

EXPECTED_CATEGORIES = {
    "01-product-manual": "产品说明书",
    "02-technical-docs": "技术文档",
    "03-it-ops-sop": "IT 运维 SOP",
    "04-after-sales": "售后流程",
    "05-faq": "FAQ",
}
MIN_DOCS_PER_CATEGORY = 2
MIN_CHARS = 200

FAILURES: list[str] = []
PASSES: list[str] = []


def check(ok: bool, msg: str) -> None:
    (PASSES if ok else FAILURES).append(msg)
    print(f"  [{'PASS' if ok else 'FAIL'}] {msg}")


def main() -> int:
    print("== 1. 分类覆盖 ==")
    for folder, label in EXPECTED_CATEGORIES.items():
        check((KB / folder).is_dir(), f"分类 {folder}（{label}）存在")

    print("== 2. 文档规模 ==")
    total = 0
    total_chars = 0
    for folder, label in EXPECTED_CATEGORIES.items():
        files = sorted((KB / folder).glob("*.md"))
        check(len(files) >= MIN_DOCS_PER_CATEGORY, f"{label}: 文档数 {len(files)} >= {MIN_DOCS_PER_CATEGORY}")
        for f in files:
            total += 1
            try:
                text = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                check(False, f"{f.name}: UTF-8 解码失败")
                continue
            check(len(text.strip()) > 0, f"{f.name}: 非空")
            check(len(text) >= MIN_CHARS, f"{f.name}: 正文字数 {len(text)} >= {MIN_CHARS}")
            check(text.lstrip().startswith("# "), f"{f.name}: 以一级标题开头")
            total_chars += len(text)

    print("== 3. 汇总 ==")
    check(total >= 8, f"总文档数 {total} >= 8")
    check(total_chars >= 3000, f"总字符数 {total_chars} >= 3000")
    print(f"\n===== 结果：{len(PASSES)} PASS / {len(FAILURES)} FAIL =====")
    print(f"知识库规模：{total} 篇文档，约 {total_chars} 字符")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    raise SystemExit(main())
