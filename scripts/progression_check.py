#!/usr/bin/env python3
"""Inline checks of a progression model for the editor (spec 019), initiative #28. Stdlib only.

  python3 scripts/progression_check.py <model.json> [--graph recipe-graph.json] [-o checks.json] [--markdown out.md]

<model.json> is a spec 017 snapshot or a website stages backup (converted on the fly). Runs the lint
of progression.py, then, with --graph (recipe_graph.py compact), the completability check, and
merges both into one document keyed by milestone key: a badge (ok, warning, error) and findings
with the reason and a machine-readable fix. Same input, same bytes out. Exit code 1 on any error.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

import progression
import recipe_graph as rg

FORMAT = "arffornia.progression-check/1"
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}
# Lint errors that make the requires graph unusable: completability needs a DAG of known keys.
STRUCTURAL = {"cycle", "unknown_requirement", "duplicate_key"}


def finding(severity: str, code: str, message: str, **extra) -> dict:
    return {"severity": severity, "code": code, "message": message, **{k: v for k, v in extra.items() if v}}


def load_model(raw: dict, source: str) -> tuple[dict, list[progression.Finding]]:
    if "schema_version" in raw:
        return raw, []
    return progression.convert(raw, source=source)


def build(model: dict, graph: dict | None) -> dict:
    keys = [m["key"] for m in model["milestones"]]
    by_key = {m["key"]: m for m in model["milestones"]}
    per_milestone: dict[str, list[dict]] = collections.defaultdict(list)
    per_stage: dict[int, list[dict]] = collections.defaultdict(list)
    pack_level: list[dict] = []

    lint = progression.lint(model)
    for f in lint:
        extra = {}
        if f.code == "cycle":
            extra["path"] = f.message.split(" -> ")
        elif f.related:
            extra["requires"] = f.related[0]
        entry = finding(f.severity, f.code, f.message, **extra)
        if f.code == "cycle":
            for key in dict.fromkeys(f.related):
                per_milestone[key].append(entry)
        elif f.subject in by_key:
            per_milestone[f.subject].append(entry)
        elif f.subject.startswith("stage "):
            per_stage[int(f.subject.split()[1])].append(entry)
        else:
            pack_level.append({**entry, "subject": f.subject})

    structural = sorted({f.code for f in lint if f.code in STRUCTURAL})
    if graph is None:
        completability = "skipped: no recipe graph"
    elif structural:
        completability = f"skipped: {', '.join(structural)} in the requires graph"
    else:
        completability = "done"
        _completability(model, graph, by_key, per_milestone, per_stage, pack_level)

    milestones = {}
    for key in sorted(keys):
        found = sorted(per_milestone.get(key, []), key=_order)
        milestones[key] = {"badge": _badge(found), "graph": by_key[key]["graph"], "stage": by_key[key]["stage"],
                           "findings": found}
    stages = {str(n): {"badge": _badge(sorted(per_stage.get(n, []), key=_order)),
                       "findings": sorted(per_stage.get(n, []), key=_order)}
              for n in sorted(s["number"] for s in model["stages"])}
    codes = collections.Counter(f["code"] for m in milestones.values() for f in m["findings"])
    badges = collections.Counter(m["badge"] for m in milestones.values())
    return {
        "format": FORMAT,
        "model": {"source": model.get("source", ""), "version": model.get("version"), "status": model.get("status")},
        "recipe_graph": None if graph is None else {"recipes": len(graph["recipes"]), "entries": len(graph["entries"])},
        "completability": completability,
        "summary": {"milestones": len(keys), "ok": badges["ok"], "warning": badges["warning"],
                    "error": badges["error"], "by_code": dict(sorted(codes.items()))},
        "milestones": milestones,
        "stages": stages,
        "pack": sorted(pack_level, key=lambda f: (_order(f), f.get("subject", ""))),
    }


def _completability(model, graph, by_key, per_milestone, per_stage, pack_level) -> None:
    report = rg.check(graph, model)
    for row in report["milestones"]:
        key = row["key"]
        if row["status"] == "unreachable":
            for item, blockers in sorted(row["blockers"].items()):
                if any(b["reason"] == rg.SELF_DELIVERY for b in blockers):
                    per_milestone[key].append(finding(
                        "error", "delivers_own_unlock", f"asks to deliver {item}, which it unlocks itself", item=item))
                    continue
                per_milestone[key].append(finding(
                    "error", "not_completable",
                    f"required item {item} cannot be made with the stages open at stage {row['stage']}: {_explain(blockers)}",
                    item=item, missing=blockers, fixes=_move_fixes(key, blockers, by_key)))
        elif row["status"] == "needs_link":
            items = sorted(row["blockers"])
            links = row["proposed_links"]
            message = (f"completable only through {', '.join(links)}, which it does not require" if links
                       else "completable only through milestones it does not require; no link set found")
            if links and not row["links_verified"]:
                message += " (these links are not enough)"
            fixes = [{"action": "add_requires", "milestone": key, "requires": links,
                      "verified": row["links_verified"]}] if links else []
            per_milestone[key].append(finding("warning", "missing_link", message, items=items, fixes=fixes))

    for u in report["unusable_unlocks"]:
        per_milestone[u["milestone"]].append(finding(
            "warning", "unlock_unusable",
            f"unlocks {u['item']}, which cannot be made right after it at stage {u['stage']}: {_explain(u['missing'])}",
            item=u["item"], missing=u["missing"], fixes=_move_fixes(u["milestone"], u["missing"], by_key)))

    for b in report["backward_links"]:
        for f in per_milestone[b["milestone"]]:
            if f["code"] == "requires_later_stage" and f.get("requires") == b["requires"]:
                f["needed_by_recipes"] = b["needed"]
                f["fixes"] = [b["fix_action"]]

    for n in report["never_craftable"]:
        for key in n["unlocked_by"]:
            per_milestone[key].append(finding(
                "error", "never_craftable", f"unlocks {n['item']}, which no player can make even with every milestone done",
                item=n["item"]))

    for leak in report["leaks"]:
        for key in leak["unlocked_by"]:
            per_milestone[key].append(finding(
                "warning", "leak", f"unlocks {leak['item']}, but recipe {leak['recipe']} still makes it with no milestone done",
                item=leak["item"], recipe=leak["recipe"],
                fixes=[{"action": "ban_recipe", "milestone": key, "item": leak["item"], "recipe": leak["recipe"]}]))

    unknown = set(report["unknown_items"])
    recipe_ids = {row[3] for row in graph["recipes"]} | set(graph.get("skipped_recipes", []))
    for m in model["milestones"]:
        validation = m.get("validation") or {}
        referenced = [u["item"] for u in m["unlocks"]] + (
            [i["item"] for i in validation["items"]] if validation.get("type") == "deliver" else [])
        for item in sorted(set(referenced) & unknown):
            per_milestone[m["key"]].append(finding("error", "unknown_item", f"{item} is not in the recipe dump", item=item))
        for unlock in m["unlocks"]:
            bans = set(unlock["recipes_to_ban"])
            # A stray id next to a real ban is noise; a ban list where nothing matches bans nothing.
            severity = "info" if bans & recipe_ids else "warning"
            for recipe in sorted(bans - recipe_ids):
                per_milestone[m["key"]].append(finding(
                    severity, "unknown_ban", f"bans {recipe} for {unlock['item']}, but no such recipe is in the dump",
                    item=unlock["item"], recipe=recipe))

    status = {row["key"]: row["status"] for row in report["milestones"]}
    for stage in model["stages"]:
        rows = [k for k, m in by_key.items() if m["stage"] == stage["number"]]
        if not rows:
            continue
        completable = sum(status[k] in ("ok", "needs_link") for k in rows)
        if completable / len(rows) < stage["threshold"]:
            per_stage[stage["number"]].append(finding(
                "error", "threshold_unreachable",
                f"{completable} of {len(rows)} milestones are completable, below the {stage['threshold']:.0%} threshold"))

    if report["guessed_machines"]:
        pack_level.append(finding("info", "guessed_machines",
                                  f"{len(report['guessed_machines'])} recipe types matched to a machine by name",
                                  subject="recipe graph"))


def _explain(blockers: list[dict]) -> str:
    return "; ".join(f"{b['item']} ({', '.join(b['unlocked_by'])})" if b["unlocked_by"] else f"{b['item']} ({b['reason']})"
                     for b in blockers) or "no blocker found"


def _move_fixes(key: str, blockers: list[dict], by_key: dict) -> list[dict]:
    """The usual fix for an item gated later: move this milestone to the stage of the latest unlocker."""
    stages = [min(by_key[k]["stage"] for k in b["unlocked_by"]) for b in blockers if b["unlocked_by"]]
    if not stages or len(stages) != len(blockers) or max(stages) <= by_key[key]["stage"]:
        return []
    return [{"action": "move_stage", "milestone": key, "stage": max(stages)}]


def _order(f: dict) -> tuple:
    return SEVERITY_ORDER[f["severity"]], f["code"], f.get("item", ""), f["message"]


def _badge(findings: list[dict]) -> str:
    severities = {f["severity"] for f in findings}
    return "error" if "error" in severities else "warning" if "warning" in severities else "ok"


def markdown(doc: dict) -> str:
    s = doc["summary"]
    lines = [f"Completability: {doc['completability']}", "",
             "| Badge | Milestones |", "|---|---|",
             f"| error | {s['error']} |", f"| warning | {s['warning']} |", f"| ok | {s['ok']} |", "",
             "| Code | Findings |", "|---|---|"]
    lines += [f"| `{code}` | {n} |" for code, n in s["by_code"].items()]
    stage_rows = [(n, f) for n, st in doc["stages"].items() for f in st["findings"] if f["severity"] != "info"]
    if stage_rows:
        lines += ["", "| Stage | Code | Message |", "|---|---|---|"]
        lines += [f"| {n} | `{f['code']}` | {f['message']} |" for n, f in stage_rows]
    rows = [(m["stage"], key, f) for key, m in doc["milestones"].items() for f in m["findings"] if f["severity"] == "error"]
    if rows:
        lines += ["", "| Stage | Milestone | Code | Message |", "|---|---|---|---|"]
        lines += [f"| {stage} | `{key}` | `{f['code']}` | {f['message']} |" for stage, key, f in sorted(rows, key=lambda r: (r[0], r[1]))]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("model", type=pathlib.Path)
    parser.add_argument("--graph", type=pathlib.Path, help="output of recipe_graph.py compact")
    parser.add_argument("-o", "--output", type=pathlib.Path, help="checks JSON (default: stdout)")
    parser.add_argument("--markdown", type=pathlib.Path)
    args = parser.parse_args(argv)

    model, _ = load_model(json.loads(args.model.read_text(encoding="utf-8")), args.model.name)
    graph = json.loads(args.graph.read_text(encoding="utf-8")) if args.graph else None
    doc = build(model, graph)
    output = json.dumps(doc, indent=1, ensure_ascii=False)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    text = markdown(doc)
    if args.markdown:
        args.markdown.write_text(text + "\n", encoding="utf-8")
    if args.output:
        print(text)
    return 1 if doc["summary"]["error"] or any(st["badge"] == "error" for st in doc["stages"].values()) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
