#!/usr/bin/env python3
"""Progression model tools (spec 017). Stdlib only.

  python3 scripts/progression.py convert <website-backup.json> [-o model.json]
  python3 scripts/progression.py lint <model.json> [--json]

`convert` turns a website stages backup (graphs, stages, milestones, milestone_closure) into a
snapshot that follows progression-model.schema.json. `lint` checks the rules of spec 017 that a
schema cannot express. Exit code 1 when lint finds an error.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, asdict

PLACEHOLDER_DESCRIPTION = "A new adventure begins..."
DEFAULT_THRESHOLD = 0.8
ITEM_ID = re.compile(r"^#?[a-z0-9_.-]+:[a-z0-9_./-]+$")


@dataclass(frozen=True)
class Finding:
    severity: str  # error | warning | info
    code: str
    subject: str
    message: str


def slug(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_") or "unnamed"


def text(value: str | None) -> dict:
    return {"en": value or ""}


def _dominant_namespace(milestones: list[dict]) -> str | None:
    namespaces = collections.Counter(
        unlock["item_id"].split(":", 1)[0]
        for milestone in milestones
        for unlock in milestone.get("unlocks", [])
        if ":" in unlock.get("item_id", "")
    )
    namespaces.pop("minecraft", None)
    return namespaces.most_common(1)[0][0] if namespaces else None


def convert(backup: dict, source: str = "") -> tuple[dict, list[Finding]]:
    findings: list[Finding] = []
    stage_number = {stage["id"]: stage["number"] for stage in backup["stages"]}
    graph_rows = {graph["id"]: graph for graph in backup["graphs"]}
    milestones_by_graph: dict[int | None, list[dict]] = collections.defaultdict(list)
    for milestone in backup["milestones"]:
        milestones_by_graph[milestone.get("graph_id")].append(milestone)

    graph_key: dict[int | None, str] = {}
    graphs = []
    used_graph_keys: set[str] = set()
    for graph_id, rows in sorted(milestones_by_graph.items(), key=lambda kv: (kv[0] is None, kv[0] or 0)):
        row = graph_rows.get(graph_id)
        key = slug(row["name"]) if row else "arffornia"
        while key in used_graph_keys:
            key += "_2"
        used_graph_keys.add(key)
        graph_key[graph_id] = key
        icon = row.get("icon_item_id") if row else None
        graph = {
            "key": key,
            "name": text(row["name"] if row else "Arffornia"),
            "mod_id": _dominant_namespace(rows),
            "branch": "neutral",
        }
        if icon and ITEM_ID.match(icon):
            graph["icon_item"] = icon
        graphs.append(graph)

    milestone_key: dict[int, str] = {}
    used_keys: set[str] = set()
    for milestone in backup["milestones"]:
        base = f"{graph_key[milestone.get('graph_id')]}/{slug(milestone['name'])}"
        key, n = base, 2
        while key in used_keys:
            key, n = f"{base}_{n}", n + 1
        used_keys.add(key)
        milestone_key[milestone["id"]] = key

    requires: dict[int, list[str]] = collections.defaultdict(list)
    for link in backup.get("milestone_closure", []):
        parent, child = link["milestone_id"], link["descendant_id"]
        if parent not in milestone_key or child not in milestone_key:
            missing = parent if parent not in milestone_key else child
            findings.append(Finding("warning", "dangling_link", f"link {link['id']}",
                                    f"points to milestone {missing}, which no longer exists; dropped"))
            continue
        if milestone_key[parent] not in requires[child]:
            requires[child].append(milestone_key[parent])

    milestones = []
    for milestone in backup["milestones"]:
        requirements = [r for r in milestone.get("requirements", []) if ITEM_ID.match(r.get("item_id", ""))]
        unlocked_items = [u["item_id"] for u in milestone.get("unlocks", []) if ITEM_ID.match(u.get("item_id", ""))]
        if requirements:
            validation = {"type": "deliver",
                          "items": [{"item": r["item_id"], "count": max(1, int(r["amount"]))} for r in requirements]}
        elif unlocked_items:
            validation = {"type": "obtain", "items": sorted(set(unlocked_items))}
        else:
            validation = None
        unlocks = []
        for unlock in milestone.get("unlocks", []):
            if not ITEM_ID.match(unlock.get("item_id", "")):
                findings.append(Finding("warning", "bad_item_id", milestone_key[milestone["id"]],
                                        f"unlock item {unlock.get('item_id')!r} is not a valid id; dropped"))
                continue
            recipe = unlock.get("recipe")
            unlocks.append({
                "item": unlock["item_id"],
                "gate_mode": "machine" if recipe else "crafting",
                "recipes_to_ban": list(unlock.get("recipes_to_ban") or []),
                "recipe": {k: recipe[k] for k in ("type", "ingredients", "result", "energy", "time") if k in recipe} if recipe else None,
                "shop_price": unlock.get("shop_price"),
            })
        entry = {
            "key": milestone_key[milestone["id"]],
            "graph": graph_key[milestone.get("graph_id")],
            "stage": stage_number[milestone["stage_id"]],
            "title": text(milestone["name"]),
            "requires": requires[milestone["id"]],
            "validation": validation,
            "unlocks": unlocks,
            "effort": None,
            "power": None,
            "source": "legacy",
            "layout": {"x": int(milestone.get("x", 0)), "y": int(milestone.get("y", 0))},
        }
        if milestone.get("description"):
            entry["description"] = text(milestone["description"])
        if milestone.get("icon_type"):
            entry["icon_type"] = milestone["icon_type"]
        milestones.append(entry)

    stages = [{
        "number": stage["number"],
        "name": text(stage["name"]),
        "description": text(stage.get("description")),
        "threshold": DEFAULT_THRESHOLD,
        "module": [],
    } for stage in sorted(backup["stages"], key=lambda s: s["number"])]

    model = {"schema_version": 1, "version": 0, "status": "draft", "source": source,
             "stages": stages, "graphs": graphs, "milestones": milestones}
    return model, findings


def lint(model: dict) -> list[Finding]:
    findings: list[Finding] = []
    stages = {stage["number"] for stage in model["stages"]}
    graphs = {graph["key"] for graph in model["graphs"]}
    by_key: dict[str, dict] = {}
    for milestone in model["milestones"]:
        if milestone["key"] in by_key:
            findings.append(Finding("error", "duplicate_key", milestone["key"], "two milestones share this key"))
        by_key[milestone["key"]] = milestone

    for milestone in model["milestones"]:
        key = milestone["key"]
        if milestone["stage"] not in stages:
            findings.append(Finding("error", "unknown_stage", key, f"stage {milestone['stage']} does not exist"))
        if milestone["graph"] not in graphs:
            findings.append(Finding("error", "unknown_graph", key, f"graph {milestone['graph']} does not exist"))
        if milestone["validation"] is None:
            findings.append(Finding("warning", "no_validation", key, "nothing completes this milestone"))
        description = milestone.get("description", {}).get("en", "")
        if not description or description == PLACEHOLDER_DESCRIPTION:
            findings.append(Finding("info", "placeholder_description", key, "description is empty or the placeholder"))
        for required in milestone["requires"]:
            parent = by_key.get(required)
            if parent is None:
                findings.append(Finding("error", "unknown_requirement", key, f"requires {required}, which does not exist"))
                continue
            if parent["stage"] > milestone["stage"]:
                findings.append(Finding("error", "requires_later_stage", key,
                                        f"stage {milestone['stage']} requires {required} from stage {parent['stage']}"))
            if parent["graph"] != milestone["graph"]:
                findings.append(Finding("info", "cross_graph", key, f"requires {required} from another graph"))

    findings.extend(_cycles(by_key))

    per_stage = collections.Counter(m["stage"] for m in model["milestones"])
    for number in sorted(stages):
        if per_stage[number] == 0:
            findings.append(Finding("warning", "empty_stage", f"stage {number}", "no milestone on this stage"))
    return findings


def _cycles(by_key: dict[str, dict]) -> list[Finding]:
    findings, state = [], {}

    def visit(key: str, path: list[str]) -> None:
        state[key] = "open"
        for required in by_key[key]["requires"]:
            if required not in by_key:
                continue
            if state.get(required) == "open":
                cycle = path[path.index(required):] + [required] if required in path else [key, required]
                findings.append(Finding("error", "cycle", key, " -> ".join(cycle)))
            elif required not in state:
                visit(required, path + [required])
        state[key] = "done"

    for key in by_key:
        if key not in state:
            visit(key, [key])
    return findings


def _report(findings: list[Finding]) -> str:
    order = {"error": 0, "warning": 1, "info": 2}
    counts = collections.Counter((f.severity, f.code) for f in findings)
    lines = [f"{severity:7} {code:26} {n}" for (severity, code), n in sorted(counts.items(), key=lambda kv: (order[kv[0][0]], kv[0][1]))]
    lines.append("")
    lines += [f"{f.severity:7} {f.code:26} {f.subject}: {f.message}"
              for f in sorted(findings, key=lambda f: (order[f.severity], f.code, f.subject)) if f.severity != "info"]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    convert_cmd = sub.add_parser("convert")
    convert_cmd.add_argument("backup")
    convert_cmd.add_argument("-o", "--output")
    lint_cmd = sub.add_parser("lint")
    lint_cmd.add_argument("model")
    lint_cmd.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "convert":
        with open(args.backup, encoding="utf-8") as fh:
            model, findings = convert(json.load(fh), source=args.backup.rsplit("/", 1)[-1])
        output = json.dumps(model, ensure_ascii=False, indent=1)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(output + "\n")
        else:
            print(output)
        if findings:
            print(_report(findings), file=sys.stderr)
        return 0

    with open(args.model, encoding="utf-8") as fh:
        findings = lint(json.load(fh))
    print(json.dumps([asdict(f) for f in findings], indent=1) if args.json else _report(findings))
    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
