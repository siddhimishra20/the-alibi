import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

class CaseRegistry:
    """Manages the persistent master registry of daily micro-crimes, ensuring zero duplicate seeds and tracking archive history."""

    def __init__(self, registry_path: str = "data/case_registry.json", cases_dir: str = "cases"):
        self.registry_path = registry_path
        self.cases_dir = cases_dir
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        os.makedirs(self.cases_dir, exist_ok=True)
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "schedule": {},
            "used_seed_ids": [],
            "used_titles": [],
            "used_suspects": [],
            "last_generated_date": None
        }

    def _save(self):
        try:
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    def rebuild_indices(self):
        """Reconstruct used_seed_ids, used_titles, and used_suspects from the active schedule."""
        seeds = set()
        titles = set()
        suspects = set()
        for d, entry in self.data.get("schedule", {}).items():
            if entry.get("seed_id"):
                seeds.add(entry["seed_id"])
            if entry.get("title"):
                titles.add(entry["title"])
            if entry.get("suspect_name"):
                suspects.add(entry["suspect_name"])
        self.data["used_seed_ids"] = sorted(list(seeds))
        self.data["used_titles"] = sorted(list(titles))
        self.data["used_suspects"] = sorted(list(suspects))
        self._save()

    def is_case_unique(self, title: str, suspect_name: str, seed_id: Optional[str] = None, exclude_date: Optional[str] = None) -> bool:
        """Check if a case title, suspect name, or seed_id has already been used on any other date."""
        for d, entry in self.data.get("schedule", {}).items():
            if exclude_date and d == exclude_date:
                continue
            if title and entry.get("title", "").strip().lower() == title.strip().lower():
                return False
            if suspect_name and entry.get("suspect_name", "").strip().lower() == suspect_name.strip().lower():
                return False
            if seed_id and entry.get("seed_id") == seed_id:
                return False
        return True

    def unregister_case(self, date_str: str):
        """Remove a date from the schedule and rebuild tracking indices."""
        if date_str in self.data.get("schedule", {}):
            del self.data["schedule"][date_str]
            self.rebuild_indices()

    def is_date_registered(self, date_str: str) -> bool:
        """Check if a date has already been registered in the schedule."""
        return date_str in self.data.get("schedule", {})

    def get_registered_entry(self, date_str: str) -> Optional[Dict[str, Any]]:
        return self.data.get("schedule", {}).get(date_str)

    def register_case(self, date_str: str, case_data: Dict[str, Any], seed_id: Optional[str] = None):
        """Register a case into the master schedule and track seed/title to prevent repeats."""
        title = case_data.get("title", "")
        suspect = case_data.get("suspect", {})
        suspect_name = suspect.get("name", "") if isinstance(suspect, dict) else getattr(suspect, "name", "")
        setting = case_data.get("setting", "")
        crime_desc = case_data.get("crime_description", "")

        entry = {
            "id": case_data.get("id", f"case-{date_str}"),
            "date": date_str,
            "title": title,
            "suspect_name": suspect_name,
            "setting": setting,
            "crime_description": crime_desc,
            "seed_id": seed_id,
            "registered_at": datetime.now().isoformat()
        }

        self.data["schedule"][date_str] = entry

        if seed_id and seed_id not in self.data["used_seed_ids"]:
            self.data["used_seed_ids"].append(seed_id)
        if title and title not in self.data["used_titles"]:
            self.data["used_titles"].append(title)
        if suspect_name and suspect_name not in self.data["used_suspects"]:
            self.data["used_suspects"].append(suspect_name)

        self.data["last_generated_date"] = date_str
        self._save()

    def get_used_seed_ids(self) -> List[str]:
        return list(self.data.get("used_seed_ids", []))

    def get_recent_suspects_and_titles(self, limit: int = 8) -> Tuple[List[str], List[str]]:
        """Return recently used suspect names and titles to pass as negative constraints to the LLM."""
        titles = list(self.data.get("used_titles", []))[-limit:]
        suspects = list(self.data.get("used_suspects", []))[-limit:]
        return titles, suspects

    def get_archive_list(self, progress_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Return list of historical and registered cases sorted by date with player status."""
        today = datetime.now().strftime("%Y-%m-%d")
        completed_dates = progress_data.get("completed_dates", {}) if progress_data else {}
        archive = []

        # Gather from both registry and existing files on disk
        dates_seen = set()

        for d_str, meta in sorted(self.data.get("schedule", {}).items()):
            dates_seen.add(d_str)
            comp = completed_dates.get(d_str)
            status = "SOLVED" if (comp and comp.get("won")) else ("FAILED" if comp else ("TODAY" if d_str == today else "READY"))
            archive.append({
                "date": d_str,
                "title": meta.get("title", "Unknown Case"),
                "suspect_name": meta.get("suspect_name", "Unknown Suspect"),
                "setting": meta.get("setting", ""),
                "status": status,
                "won": comp.get("won", False) if comp else False,
                "is_today": d_str == today,
                "file_exists": os.path.exists(os.path.join(self.cases_dir, f"{d_str}.json"))
            })

        # Also inspect cases/ directory for any orphaned JSON files
        if os.path.exists(self.cases_dir):
            for fname in os.listdir(self.cases_dir):
                if fname.endswith(".json") and fname[:-5] not in dates_seen and fname != "progress.json":
                    d_str = fname[:-5]
                    fpath = os.path.join(self.cases_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            raw = json.load(f)
                            comp = completed_dates.get(d_str)
                            status = "SOLVED" if (comp and comp.get("won")) else ("FAILED" if comp else ("TODAY" if d_str == today else "READY"))
                            susp = raw.get("suspect", {})
                            s_name = susp.get("name", "") if isinstance(susp, dict) else ""
                            archive.append({
                                "date": d_str,
                                "title": raw.get("title", f"Case {d_str}"),
                                "suspect_name": s_name or "Unknown",
                                "setting": raw.get("setting", ""),
                                "status": status,
                                "won": comp.get("won", False) if comp else False,
                                "is_today": d_str == today,
                                "file_exists": True
                            })
                    except Exception:
                        pass

        # Sort descending by date (most recent first)
        archive.sort(key=lambda x: x["date"], reverse=True)
        return archive

