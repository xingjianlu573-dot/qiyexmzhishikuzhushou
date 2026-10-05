# -*- coding: utf-8 -*-
"""通过 Dify Service API 批量创建知识库并上传 seed/knowledge-base 文档。

用法（Dify 部署完成后，在“知识库 → API 访问”中创建数据集 API Key）：
    python deploy/scripts/seed-kb.py \
        --base-url http://localhost/v1 \
        --api-key dataset-xxxxxxxxxxxx \
        [--config deploy/seed-config.json]

说明：
- 创建 5 个企业知识库数据集（产品说明书/技术文档/IT运维SOP/售后流程/FAQ）。
- 将每个分类下的 Markdown 文档上传并触发索引（high_quality + 自动分块）。
- 结束后打印数据集 ID 列表 —— 用于在应用 DSL 的「企业知识库检索」节点重新绑定。

依赖：requests（pip install requests）
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

try:
    import requests
except ImportError:  # pragma: no cover
    sys.exit("缺少依赖：请先执行 pip install requests")

DEFAULT_CONFIG = ROOT / "deploy" / "seed-config.json"


def create_dataset(base_url: str, api_key: str, name: str, description: str) -> str:
    """创建知识库数据集，返回 dataset id。"""
    resp = requests.post(
        f"{base_url}/datasets",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "name": name,
            "description": description,
            "indexing_technique": "high_quality",
            "permission": "only_me",
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def upload_documents(base_url: str, api_key: str, dataset_id: str, folder: Path) -> int:
    """上传目录下全部 Markdown 文档，返回上传数量。"""
    count = 0
    for md in sorted(folder.glob("*.md")):
        data = {
            "indexing_technique": "high_quality",
            "process_rule": json.dumps({
                "mode": "automatic",
                "rules": {"pre_processing_rules": [], "segmentation": {"separator": "\n\n", "max_tokens": 500}},
            }),
        }
        with md.open("rb") as fh:
            resp = requests.post(
                f"{base_url}/datasets/{dataset_id}/document/create",
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": (md.name, fh, "text/markdown")},
                data=data,
                timeout=120,
            )
        if resp.status_code in (200, 201):
            count += 1
            print(f"    - {md.name} OK")
        else:
            print(f"    - {md.name} FAIL: {resp.status_code} {resp.text[:200]}")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Dify 企业知识库种子数据导入")
    parser.add_argument("--base-url", required=True, help="Dify Service API 地址，如 http://localhost/v1")
    parser.add_argument("--api-key", required=True, help="数据集 API Key（dataset- 开头）")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="seed-config.json 路径")
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    dataset_ids: dict[str, str] = {}

    for item in config["datasets"]:
        folder = ROOT / item["folder"]
        print(f"[1/2] 创建知识库：{item['name']}")
        ds_id = create_dataset(args.base_url, args.api_key, item["name"], item["description"])
        dataset_ids[item["name"]] = ds_id
        print(f"    dataset_id = {ds_id}")
        print(f"[2/2] 上传文档：{item['folder']}")
        n = upload_documents(args.base_url, args.api_key, ds_id, folder)
        print(f"    共上传 {n} 篇")
        time.sleep(1)

    print("\n===== 导入完成，请记录以下 ID 用于应用 DSL 绑定 =====")
    for name, ds_id in dataset_ids.items():
        print(f"  {name}: {ds_id}")
    print("\n下一步：在 Dify 控制台导入 seed/apps/enterprise-ai-knowledge-assistant.yml，")
    print("在「企业知识库检索」节点将 dataset_ids 替换为上表 ID，并选择 LLM / Embedding / Rerank 模型。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
