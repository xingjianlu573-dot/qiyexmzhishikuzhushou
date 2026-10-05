# -*- coding: utf-8 -*-
"""校验 Dify 应用 DSL（seed/apps/enterprise-ai-knowledge-assistant.yml）。

校验项：
1. YAML 可解析，顶层 kind=app、version、app.mode=advanced-chat
2. workflow.features.retriever_resource.enabled=true（引用来源）
3. graph 节点 id 唯一、类型合法；边引用的节点存在、handle 合法
4. knowledge-retrieval 节点：dataset_ids 非空、retrieval_mode、multiple_retrieval_config 字段完整
   （top_k / score_threshold / reranking_enable / reranking_mode）
5. if-else 节点：comparison_operator 在支持集合内（对照 graphon 枚举）
6. 变量选择器引用的节点 id 存在；sys 为内置变量
7. 若可导入 graphon，则用 pydantic 模型校验 if-else 节点数据
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DSL = ROOT / "seed" / "apps" / "enterprise-ai-knowledge-assistant.yml"

SUPPORTED_OPERATORS = {
    "contains", "not contains", "start with", "end with", "is", "is not",
    "empty", "not empty", "in", "not in", "all of",
    "=", "≠", ">", "<", "≥", "≤", "null", "not null",
    "exists", "not exists",
}
KNOWN_NODE_TYPES = {"start", "llm", "answer", "knowledge-retrieval", "if-else", "end", "agent", "code", "http-request"}
NODE_HANDLES = {"source": {"source"}, "target": {"target"}}
ROUTE_HANDLES = {"true", "false"}

FAILURES: list[str] = []
PASSES: list[str] = []


def check(ok: bool, msg: str) -> None:
    (PASSES if ok else FAILURES).append(msg)
    print(f"  [{'PASS' if ok else 'FAIL'}] {msg}")


def main() -> int:
    print("== 1. 解析 DSL ==")
    if not DSL.exists():
        print(f"   [FAIL] 文件不存在: {DSL}")
        return 1
    data = yaml.safe_load(DSL.read_text(encoding="utf-8"))
    check(data.get("kind") == "app", f"kind=app (实际 {data.get('kind')!r})")
    check(bool(data.get("version")), f"version 存在 ({data.get('version')!r})")
    app = data.get("app", {})
    check(app.get("mode") == "advanced-chat", f"app.mode=advanced-chat (实际 {app.get('mode')!r})")
    check(bool(app.get("name")), f"app.name 非空 ({app.get('name')!r})")

    print("== 2. 引用来源特性 ==")
    features = data.get("workflow", {}).get("features", {})
    rr = features.get("retriever_resource", {})
    check(rr.get("enabled") is True, "features.retriever_resource.enabled=true（聊天界面引用卡片）")

    print("== 3. 图结构 ==")
    graph = data.get("workflow", {}).get("graph", {})
    nodes, edges = graph.get("nodes", []), graph.get("edges", [])
    check(len(nodes) >= 4, f"节点数量 >= 4 ({len(nodes)})")
    node_ids = [n.get("id") for n in nodes]
    check(len(node_ids) == len(set(node_ids)), "节点 id 唯一")
    node_by_id = {n["id"]: n for n in nodes}
    for n in nodes:
        ntype = n.get("data", {}).get("type")
        check(ntype in KNOWN_NODE_TYPES, f"节点 {n.get('id')} 类型合法 ({ntype})")

    edge_ok = True
    for e in edges:
        if e.get("source") not in node_by_id or e.get("target") not in node_by_id:
            edge_ok = False
            print(f"  [FAIL] 边引用不存在节点: {e.get('id')}")
    check(edge_ok, "所有边的 source/target 均存在")
    # route 节点的 true/false handle
    for e in edges:
        if e.get("source") == "route":
            h = e.get("sourceHandle")
            check(h in ROUTE_HANDLES, f"route 输出 handle 合法 ({h})")

    print("== 4. knowledge-retrieval 节点 ==")
    kr = node_by_id.get("knowledge_retrieval", {}).get("data", {})
    check(bool(kr.get("dataset_ids")), "dataset_ids 非空（导入后需重新绑定数据集）")
    check(kr.get("retrieval_mode") == "multiple", f"retrieval_mode=multiple ({kr.get('retrieval_mode')!r})")
    mrc = kr.get("multiple_retrieval_config") or {}
    check(isinstance(mrc.get("top_k"), int) and mrc.get("top_k") > 0, f"top_k 有效 ({mrc.get('top_k')})")
    check(isinstance(mrc.get("score_threshold"), (int, float)), f"score_threshold 存在 ({mrc.get('score_threshold')})")
    check(mrc.get("reranking_enable") is True, "reranking_enable=true（重排控制检索质量）")
    check(mrc.get("reranking_mode") == "reranking_model", f"reranking_mode ({mrc.get('reranking_mode')!r})")
    check(kr.get("query_variable_selector") == ["sys", "query"], "query_variable_selector=[sys, query]")

    print("== 5. if-else 节点 ==")
    ife = node_by_id.get("route", {}).get("data", {})
    cases = ife.get("cases") or []
    check(len(cases) >= 1, f"cases 非空 ({len(cases)})")
    ops_ok = True
    for case in cases:
        for cond in case.get("conditions", []):
            op = cond.get("comparison_operator")
            if op not in SUPPORTED_OPERATORS:
                ops_ok = False
                print(f"  [FAIL] 不支持的操作符: {op!r}")
            sel = cond.get("variable_selector", [])
            if len(sel) == 2 and sel[0] not in ("sys",) and sel[0] not in node_by_id:
                ops_ok = False
                print(f"  [FAIL] 条件变量选择器引用不存在节点: {sel}")
    check(ops_ok, "conditions 操作符与变量引用合法")

    print("== 6. 变量选择器引用 ==")
    sel_ok = True
    for n in nodes:
        data = n.get("data", {})
        ctx = data.get("context", {})
        if ctx.get("enabled"):
            vs = ctx.get("variable_selector", [])
            if vs and vs[0] not in node_by_id:
                sel_ok = False
                print(f"  [FAIL] 上下文变量引用不存在节点: {n.get('id')} -> {vs}")
        ans = data.get("answer", "")
        if isinstance(ans, str) and "{{#" in ans:
            import re
            for ref in re.findall(r"\{\{#([\w-]+)\.", ans):
                if ref not in node_by_id:
                    sel_ok = False
                    print(f"  [FAIL] answer 模板引用不存在节点: {ref}")
    check(sel_ok, "模板变量引用节点均存在")

    print("== 7. graphon pydantic 校验 ==")
    graphon_ok = True
    try:
        import importlib.util
        import types

        ext = ROOT.parent / "graphon_pkg" / "extracted"
        sys.path.insert(0, str(ext))

        def _stub_pkg(name: str, path: Path) -> None:
            m = types.ModuleType(name)
            m.__path__ = [str(path)]
            sys.modules[name] = m

        def _load(name: str, path: Path):
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            return mod

        # 用桩包绕开重依赖的包 __init__（graphon 本体根/子包）
        _stub_pkg("graphon", ext / "graphon")
        _stub_pkg("graphon.nodes", ext / "graphon" / "nodes")
        _stub_pkg("graphon.nodes.if_else", ext / "graphon" / "nodes" / "if_else")
        _stub_pkg("graphon.entities", ext / "graphon" / "entities")
        import graphon.enums  # noqa: F401  轻量
        _load("graphon.entities.base_node_data", ext / "graphon" / "entities" / "base_node_data.py")
        _load("graphon.utils.condition.entities", ext / "graphon" / "utils" / "condition" / "entities.py")
        ife_mod = _load("graphon.nodes.if_else.entities", ext / "graphon" / "nodes" / "if_else" / "entities.py")

        model = ife_mod.IfElseNodeData.model_validate(ife)
        check(bool(model.cases), "IfElseNodeData.model_validate 通过（graphon 0.7.0 schema）")
        case = model.cases[0]
        check(
            case.conditions[0].comparison_operator == "not empty",
            f"条件操作符='not empty'（实际 {case.conditions[0].comparison_operator!r}）",
        )
        check(
            case.conditions[0].variable_selector == ["knowledge_retrieval", "result"],
            f"条件变量=[knowledge_retrieval, result]（实际 {case.conditions[0].variable_selector}）",
        )
        del sys.path[0]
    except Exception as exc:  # noqa: BLE001
        graphon_ok = False
        print(f"  [FAIL] graphon 校验异常：{type(exc).__name__}: {exc}")

    print(f"\n===== 结果：{len(PASSES)} PASS / {len(FAILURES)} FAIL =====")
    return 0 if not FAILURES and graphon_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
