#!/usr/bin/env python3
"""Findings manager: persist research findings to JSON, query and summarize."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


class FindingsDB:
    """Manages a persistent JSON store of research findings."""

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.file = self.workspace / "findings.json"
        self._data = self._load()

    def _load(self) -> dict:
        if self.file.exists():
            with open(self.file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "question": "",
            "sub_questions": [],
            "findings": [],
            "gaps": [],
            "status": "init",  # init | researching | synthesizing | done
            "created_at": "",
            "updated_at": "",
            "round": 0,
        }

    def _save(self):
        self._data["updated_at"] = datetime.now().isoformat()
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def init_research(self, question: str, sub_questions: list[str]):
        self._data["question"] = question
        self._data["sub_questions"] = sub_questions
        self._data["status"] = "researching"
        self._data["created_at"] = datetime.now().isoformat()
        self._data["round"] = 0
        self._data["findings"] = []
        self._data["gaps"] = []
        self._save()

    def next_round(self) -> int:
        self._data["round"] += 1
        self._save()
        return self._data["round"]

    def add_finding(self, sub_question: str, content: str, source_url: str,
                    source_name: str, relevance: str = "high",
                    finding_type: str = "fact", key_data: str = ""):
        """Add a single finding. relevance: high/medium/low. type: fact/opinion/data/perspective"""
        finding = {
            "id": len(self._data["findings"]) + 1,
            "round": self._data["round"],
            "sub_question": sub_question,
            "content": content,
            "source_url": source_url,
            "source_name": source_name,
            "relevance": relevance,
            "type": finding_type,
            "key_data": key_data,
            "added_at": datetime.now().isoformat(),
        }
        self._data["findings"].append(finding)
        self._save()
        return finding["id"]

    def add_gap(self, gap: str, priority: str = "high"):
        """Record an information gap. priority: high/medium/low"""
        self._data["gaps"].append({
            "description": gap,
            "priority": priority,
            "identified_at": datetime.now().isoformat(),
            "resolved": False,
        })
        self._save()

    def resolve_gap(self, gap_description: str):
        for gap in self._data["gaps"]:
            if gap_description in gap["description"] or gap["description"] in gap_description:
                gap["resolved"] = True
        self._save()

    def get_unresolved_gaps(self) -> list[dict]:
        return [g for g in self._data["gaps"] if not g["resolved"]]

    def get_findings_by_subq(self, sub_question: str) -> list[dict]:
        return [f for f in self._data["findings"] if f["sub_question"] == sub_question]

    def get_high_relevance_findings(self) -> list[dict]:
        return [f for f in self._data["findings"] if f["relevance"] == "high"]

    def get_all_findings(self) -> list[dict]:
        return self._data["findings"]

    def get_stats(self) -> dict:
        return {
            "round": self._data["round"],
            "total_findings": len(self._data["findings"]),
            "high_relevance": len([f for f in self._data["findings"] if f["relevance"] == "high"]),
            "unresolved_gaps": len(self.get_unresolved_gaps()),
            "sub_questions": len(self._data["sub_questions"]),
            "sub_questions_covered": len(set(f["sub_question"] for f in self._data["findings"])),
            "sources": len(set(f["source_url"] for f in self._data["findings"] if f["source_url"])),
        }

    def set_status(self, status: str):
        self._data["status"] = status
        self._save()

    def get_status(self) -> str:
        return self._data["status"]

    def export_for_report(self) -> dict:
        """Export structured data for report generation."""
        # Group findings by sub_question
        by_subq = {}
        for f in self._data["findings"]:
            sq = f["sub_question"]
            if sq not in by_subq:
                by_subq[sq] = []
            by_subq[sq].append(f)

        # Build source index
        sources = {}
        for f in self._data["findings"]:
            url = f["source_url"]
            if url and url not in sources:
                sources[url] = {
                    "name": f["source_name"],
                    "url": url,
                    "cited_count": 0,
                }
            if url and url in sources:
                sources[url]["cited_count"] += 1

        return {
            "question": self._data["question"],
            "sub_questions": self._data["sub_questions"],
            "findings_by_subq": by_subq,
            "all_findings": self._data["findings"],
            "sources": list(sources.values()),
            "gaps": self._data["gaps"],
            "stats": self.get_stats(),
            "rounds": self._data["round"],
        }


def main():
    """CLI interface for findings management."""
    import argparse
    parser = argparse.ArgumentParser(description="Research findings manager")
    sub = parser.add_subparsers(dest="cmd")

    # init
    p_init = sub.add_parser("init")
    p_init.add_argument("--workspace", required=True)
    p_init.add_argument("--question", required=True)
    p_init.add_argument("--sub-questions", nargs="+", required=True)

    # add
    p_add = sub.add_parser("add")
    p_add.add_argument("--workspace", required=True)
    p_add.add_argument("--sub-question", required=True)
    p_add.add_argument("--content", required=True)
    p_add.add_argument("--url", default="")
    p_add.add_argument("--source", default="")
    p_add.add_argument("--relevance", default="high")
    p_add.add_argument("--type", default="fact")
    p_add.add_argument("--key-data", default="")

    # gap
    p_gap = sub.add_parser("gap")
    p_gap.add_argument("--workspace", required=True)
    p_gap.add_argument("--description", required=True)
    p_gap.add_argument("--priority", default="high")

    # stats
    p_stats = sub.add_parser("stats")
    p_stats.add_argument("--workspace", required=True)

    # export
    p_export = sub.add_parser("export")
    p_export.add_argument("--workspace", required=True)
    p_export.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.cmd == "init":
        db = FindingsDB(args.workspace)
        db.init_research(args.question, args.sub_questions)
        print(f"Research initialized: {args.workspace}")

    elif args.cmd == "add":
        db = FindingsDB(args.workspace)
        fid = db.add_finding(
            sub_question=args.sub_question,
            content=args.content,
            source_url=args.url,
            source_name=args.source,
            relevance=args.relevance,
            finding_type=args.type,
            key_data=args.key_data,
        )
        print(f"Finding #{fid} added")

    elif args.cmd == "gap":
        db = FindingsDB(args.workspace)
        db.add_gap(args.description, args.priority)
        print(f"Gap recorded: {args.description}")

    elif args.cmd == "stats":
        db = FindingsDB(args.workspace)
        stats = db.get_stats()
        for k, v in stats.items():
            print(f"  {k}: {v}")

    elif args.cmd == "export":
        db = FindingsDB(args.workspace)
        data = db.export_for_report()
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Exported to {args.output}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
