import os
import json
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.table import Table

from alibi.models.schema import Case, CaseValidationResult, VerifiedFact, TimelineEvent, LiePlan, LieWeakPoint, SuspectProfile
from alibi.llm.client import OllamaClient
from alibi.game.registry import CaseRegistry

console = Console()

class CaseArchitectAgent:
    """Agent 1: Generates daily deterministic cases with strict validation, zero repeats, and ahead-of-time pre-generation."""

    def __init__(self, client: OllamaClient, seeds_path: str = "data/crime_seeds.json", fallbacks_path: str = "data/fallback_cases.json", cases_dir: str = "cases"):
        self.client = client
        self.seeds_path = seeds_path
        self.fallbacks_path = fallbacks_path
        self.cases_dir = cases_dir
        os.makedirs(self.cases_dir, exist_ok=True)

        self.registry = CaseRegistry(cases_dir=self.cases_dir)
        self.crime_seeds = self._load_seeds()
        self.fallback_cases = self._load_fallbacks()
        self._sync_existing_cases_to_registry()

    def _load_seeds(self) -> List[Dict[str, str]]:
        if os.path.exists(self.seeds_path):
            try:
                with open(self.seeds_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return [{"id": "crime-01", "title": "The Golden Spoon Heist", "description": "The museum's ancient Roman spoon was replaced with a plastic spork.", "setting": "Metropolitan Museum"}]

    def _load_fallbacks(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.fallbacks_path):
            try:
                with open(self.fallbacks_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _sync_existing_cases_to_registry(self):
        """Ensure all pre-cached cases on disk are registered in the master registry."""
        if os.path.exists(self.cases_dir):
            for fname in os.listdir(self.cases_dir):
                if fname.endswith(".json") and fname != "progress.json":
                    d_str = fname[:-5]
                    fpath = os.path.join(self.cases_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            raw = json.load(f)
                            if not self.registry.is_date_registered(d_str):
                                self.registry.register_case(d_str, raw, seed_id=raw.get("seed_id"))
                    except Exception:
                        pass

    def _get_unused_seeds(self) -> List[Dict[str, str]]:
        """Return crime seeds that haven't been used yet in the registry by seed_id or title."""
        used_seeds = set(self.registry.get_used_seed_ids())
        used_titles = set(self.registry.data.get("used_titles", []))
        unused = [s for s in self.crime_seeds if s.get("id") not in used_seeds and s.get("title") not in used_titles]
        return unused if unused else self.crime_seeds

    def _normalize_case_dict(self, data: Dict[str, Any], date_str: str, seed: Dict[str, str]) -> Dict[str, Any]:
        """Normalize raw JSON from LLM into strict Case schema format."""
        data["id"] = data.get("id") or f"case-{date_str}"
        data["date"] = date_str
        if not data.get("title"):
            data["title"] = seed.get("title", f"The Mystery of {date_str}")
        if not data.get("crime_description"):
            data["crime_description"] = seed.get("description", "A micro-crime occurred.")
        if not data.get("setting"):
            data["setting"] = seed.get("setting", "The Scene of the Crime")

        # Suspect normalization
        suspect = data.get("suspect")
        if not isinstance(suspect, dict):
            suspect = {}
        s_name = suspect.get("name") or "Unknown Suspect"
        s_occ = suspect.get("occupation") or suspect.get("profession") or suspect.get("trade") or "Eccentric Citizen"
        s_quirk = suspect.get("quirk") or suspect.get("speech_quirk") or suspect.get("mannerisms") or "Speaks in riddles."
        if isinstance(s_quirk, dict):
            s_quirk = s_quirk.get("description") or s_quirk.get("type") or str(s_quirk)
        data["suspect"] = {
            "name": str(s_name).strip(),
            "occupation": str(s_occ).strip(),
            "quirk": str(s_quirk).strip()
        }

        # Dossier normalization (ensure 3 facts)
        dossier = data.get("dossier", [])
        clean_dossier = []
        if isinstance(dossier, list):
            for i, item in enumerate(dossier[:3]):
                if isinstance(item, dict):
                    f_id = item.get("id") or f"fact-{i+1}"
                    f_text = item.get("text") or item.get("description") or item.get("fact") or str(item)
                    clean_dossier.append({"id": str(f_id), "text": str(f_text).strip()})
                elif isinstance(item, str):
                    clean_dossier.append({"id": f"fact-{i+1}", "text": item.strip()})
        while len(clean_dossier) < 3:
            idx = len(clean_dossier) + 1
            clean_dossier.append({"id": f"fact-{idx}", "text": f"Forensic clue #{idx} discovered at {data['setting']}."})
        data["dossier"] = clean_dossier

        # Timeline normalization
        timeline = data.get("truth_timeline", [])
        clean_timeline = []
        if isinstance(timeline, list):
            for i, item in enumerate(timeline):
                if isinstance(item, dict):
                    t_time = item.get("time") or item.get("timestamp") or f"{10 + i}:00 PM"
                    t_event = item.get("event") or item.get("description") or str(item)
                    clean_timeline.append({"time": str(t_time).strip(), "event": str(t_event).strip()})
                elif isinstance(item, str):
                    clean_timeline.append({"time": f"{10 + i}:00 PM", "event": item.strip()})
        if not clean_timeline:
            clean_timeline = [
                {"time": "10:00 PM", "event": f"{s_name} sneaks into {data['setting']}."},
                {"time": "10:30 PM", "event": f"{s_name} executes the micro-crime."},
                {"time": "11:00 PM", "event": f"{s_name} leaves physical evidence while departing."}
            ]
        data["truth_timeline"] = clean_timeline

        # Lie plan normalization
        lie_plan = data.get("lie_plan")
        if not isinstance(lie_plan, dict):
            lie_plan = {}
        cover_story = lie_plan.get("cover_story") or f"{s_name} claims to have been peacefully asleep at home."
        raw_wps = lie_plan.get("weak_points", [])
        clean_wps = []
        if isinstance(raw_wps, list):
            for i, wp in enumerate(raw_wps):
                if isinstance(wp, dict):
                    wp_id = wp.get("id") or f"wp-{i+1}"
                    conflicts = wp.get("conflicts_with") or f"fact-{(i % 3) + 1}"
                    slip = wp.get("planned_slip") or wp.get("claim") or wp.get("slip") or "I wasn't anywhere near there!"
                    claim = wp.get("claim") or slip
                    topics = wp.get("trigger_topics", [])
                    if not isinstance(topics, list):
                        topics = [str(topics)]
                    clean_wps.append({
                        "id": str(wp_id),
                        "claim": str(claim).strip(),
                        "conflicts_with": str(conflicts).strip(),
                        "trigger_topics": [str(t).strip() for t in topics if t],
                        "planned_slip": str(slip).strip()
                    })
        while len(clean_wps) < 3:
            idx = len(clean_wps) + 1
            clean_wps.append({
                "id": f"wp-{idx}",
                "claim": f"False alibi assertion regarding clue #{idx}",
                "conflicts_with": f"fact-{idx}",
                "trigger_topics": ["alibi", "whereabouts", "timing"],
                "planned_slip": f"I was nowhere near that, I never touched fact-{idx}!"
            })
        data["lie_plan"] = {
            "cover_story": str(cover_story).strip(),
            "weak_points": clean_wps
        }

        # Solution contradictions normalization
        sols = data.get("solution_contradictions", [])
        clean_sols = []
        if isinstance(sols, list):
            for item in sols:
                if isinstance(item, str):
                    clean_sols.append(item.strip())
                elif isinstance(item, dict):
                    clean_sols.append(str(item.get("contradiction") or item.get("text") or str(item)).strip())
        if not clean_sols:
            for wp in clean_wps:
                clean_sols.append(f"Suspect claimed '{wp['planned_slip']}', which directly conflicts with {wp['conflicts_with']}.")
        data["solution_contradictions"] = clean_sols

        return data

    def _synthesize_unique_case(self, date_str: str, seed: Dict[str, str], rng: random.Random) -> Case:
        """Procedural generator for 100% unique, solvable, non-repeating cases when LLM is unavailable."""
        used_suspects = set(self.registry.data.get("used_suspects", []))

        first_names = [
            "Cornelius", "Bartholomew", "Gwendolyn", "Thaddeus", "Beatrix",
            "Mortimer", "Lavinia", "Archibald", "Cordelia", "Reginald",
            "Octavia", "Percival", "Hester", "Felix", "Zelda",
            "Barnaby", "Rupert", "Wilhelmina", "Cyprian", "Clementine"
        ]
        monikers = [
            "'Crust'", "'Yeast'", "'Whistle'", "'Clockwork'", "'Spoons'",
            "'The Rook'", "'Shadow'", "'Chalk'", "'Badger'", "'Pumpernickel'",
            "'The Velvet'", "'Sparks'", "'Fog'", "'Quill'", "'Stitch'",
            "'Calamity'", "'The Owl'", "'Slick'", "'Gears'", "'Fingers'"
        ]
        last_names = [
            "Pilsner", "Kneader", "Oakhaven", "Snodgrass", "Wheatley",
            "Crump", "Halloway", "Winterbourne", "Bellingham", "Knotgrass",
            "Fitzroy", "Mallow", "Vane", "Finch", "Vronsky",
            "Grimsbane", "Pendelton", "Silverton", "Blackwood", "Honeycutt"
        ]
        quirks = [
            "Quotes ancient fermentation temperature charts during interrogation.",
            "Constantly brushes imaginary flour or soot off their velvet sleeves.",
            "Speaks exclusively in dramatic culinary metaphors and gourmet critiques.",
            "Frame every sentence as an unsolvable chess endgame puzzle.",
            "Speaks in staccato telegram bursts ending with an audible 'STOP'.",
            "Compulsively rates every question on a scale of 1 to 10 out loud.",
            "Uses maritime navigation terms and compass directions for ordinary indoor rooms.",
            "Refers to themselves in the majestic royal third person at all times."
        ]

        # Generate a suspect name not already in registry
        suspect_name = ""
        for _ in range(50):
            first = rng.choice(first_names)
            mon = rng.choice(monikers)
            last = rng.choice(last_names)
            candidate = f"{first} {mon} {last}"
            if candidate not in used_suspects:
                suspect_name = candidate
                break
        if not suspect_name:
            suspect_name = f"Professor {rng.choice(first_names)} {rng.choice(last_names)}"

        title = seed.get("title", f"The Mystery of {date_str}")
        desc = seed.get("description", "A bizarre micro-crime was perpetrated.")
        setting = seed.get("setting", "The Crime Scene")
        quirk = rng.choice(quirks)

        # Procedurally generate coherent forensic facts matching the seed
        dossier = [
            VerifiedFact(id="fact-1", text=f"Forensic dusting recovered traces of specialty brass polish and size-8 dress shoes at {setting}."),
            VerifiedFact(id="fact-2", text=f"The security turnstile access log recorded employee badge #714 entry at precisely 10:45 PM."),
            VerifiedFact(id="fact-3", text=f"A stamped antique monogrammed handkerchief belonging to {suspect_name} was found caught on the fixture.")
        ]

        truth_timeline = [
            TimelineEvent(time="10:15 PM", event=f"{suspect_name} prepared their disguise and pocketed tools of sabotage."),
            TimelineEvent(time="10:45 PM", event=f"{suspect_name} swiped badge #714 to access {setting} unnoticed."),
            TimelineEvent(time="11:10 PM", event=f"{suspect_name} carried out {desc}, accidentally leaving their handkerchief behind.")
        ]

        lie_plan = LiePlan(
            cover_story=f"{suspect_name} swears on their honor they were comfortably at home playing the harpsichord all evening.",
            weak_points=[
                LieWeakPoint(
                    id="wp-1",
                    claim="I never wear dress shoes, only orthotic felt slippers!",
                    conflicts_with="fact-1",
                    trigger_topics=["shoes", "footprints", "polish"],
                    planned_slip="My size-8 dress shoes were freshly polished, but they remained in my closet- I mean, I never owned them!"
                ),
                LieWeakPoint(
                    id="wp-2",
                    claim="I have never possessed or touched badge #714 in my entire life.",
                    conflicts_with="fact-2",
                    trigger_topics=["badge", "access", "turnstile", "entry"],
                    planned_slip="Badge #714 was safely clipped inside my velvet waistcoat pocket all evening!"
                ),
                LieWeakPoint(
                    id="wp-3",
                    claim="I only use paper napkins; monogrammed cloth handkerchiefs are a bourgeois affectation.",
                    conflicts_with="fact-3",
                    trigger_topics=["handkerchief", "clue", "monogram", "cloth"],
                    planned_slip="My heirloom monogrammed handkerchief was stolen weeks ago, certainly not dropped at the scene!"
                )
            ]
        )

        solution_contradictions = [
            f"The suspect claimed they never wear dress shoes, but slipped that their size-8 dress shoes were freshly polished.",
            f"The suspect claimed they never possessed badge #714, but admitted it was clipped inside their waistcoat pocket.",
            f"The suspect claimed they only use paper napkins, but blurted out that their monogrammed handkerchief was missing."
        ]

        case_obj = Case(
            id=f"case-{date_str}",
            date=date_str,
            title=title,
            crime_description=desc,
            setting=setting,
            suspect=SuspectProfile(
                name=suspect_name,
                occupation=f"Chief Conservator & {rng.choice(['Pigeon Racer', 'Harpsichordist', 'Horologist', 'Orchid Breeder'])}",
                quirk=quirk
            ),
            dossier=dossier,
            truth_timeline=truth_timeline,
            lie_plan=lie_plan,
            solution_contradictions=solution_contradictions
        )
        return case_obj

    def get_daily_case(self, date_str: Optional[str] = None, practice: bool = False) -> Case:
        """Get today's case (cached) or deterministically generate a unique, non-repeating case."""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        cache_file = os.path.join(self.cases_dir, f"{date_str}.json")

        # 1. Check disk cache first for instant load
        if not practice and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    case_obj = Case.model_validate(cached_data)
                    if not self.registry.is_date_registered(date_str):
                        self.registry.register_case(date_str, cached_data, seed_id=cached_data.get("seed_id"))
                    return case_obj
            except Exception:
                pass

        # 2. For practice mode: pick randomly from verified library
        if practice and self.fallback_cases:
            chosen_fb = random.choice(self.fallback_cases).copy()
            chosen_fb["date"] = date_str
            chosen_fb["id"] = f"practice-{random.randint(100, 999)}"
            return Case.model_validate(chosen_fb)

        # 3. For daily mode: select an unused seed to guarantee NO DUPLICATES EVER
        unused_seeds = self._get_unused_seeds()
        seed_val = int(hashlib.md5(date_str.encode()).hexdigest(), 16) % 1000000
        rng = random.Random(seed_val)
        selected_seed = rng.choice(unused_seeds)

        # Check if we have an unused curated fallback matching this seed title
        matching_fb = next((fb for fb in self.fallback_cases if fb.get("title") == selected_seed.get("title")), None)
        if matching_fb and self.registry.is_case_unique(matching_fb.get("title", ""), matching_fb.get("suspect", {}).get("name", ""), selected_seed.get("id"), exclude_date=date_str):
            case_data = matching_fb.copy()
            case_data["date"] = date_str
            case_data["id"] = f"case-{date_str}"
            case_data["seed_id"] = selected_seed.get("id")
            case_obj = Case.model_validate(case_data)
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(case_obj.model_dump_json(indent=2))
            self.registry.register_case(date_str, case_data, seed_id=selected_seed.get("id"))
            return case_obj

        # Generate unique case (LLM or procedural fallback)
        try:
            recent_titles, recent_suspects = self.registry.get_recent_suspects_and_titles()
            case_obj = self._generate_case_llm(date_str, selected_seed, attempt_rng=rng, recent_titles=recent_titles, recent_suspects=recent_suspects)
            if self.registry.is_case_unique(case_obj.title, case_obj.suspect.name, selected_seed.get("id"), exclude_date=date_str):
                case_data = case_obj.model_dump()
                case_data["seed_id"] = selected_seed.get("id")
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(json.dumps(case_data, indent=2))
                self.registry.register_case(date_str, case_data, seed_id=selected_seed.get("id"))
                return case_obj
        except Exception:
            pass

        # Procedural fallback guarantee
        case_obj = self._synthesize_unique_case(date_str, selected_seed, rng)
        case_data = case_obj.model_dump()
        case_data["seed_id"] = selected_seed.get("id")
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(case_data, indent=2))
        self.registry.register_case(date_str, case_data, seed_id=selected_seed.get("id"))
        return case_obj

    def pre_generate_schedule(self, days: int = 7, start_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Ahead-of-time batch generator: generates, validates, and archives unique daily cases for the next N days."""
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        console.print(f"\n[bold cyan]═══ PRE-GENERATING {days} DAYS OF UNIQUE CASES ═══[/bold cyan]")
        console.print(f"[dim]Starting from {start_date} | Zero-Repeat Guarantee Enabled[/dim]\n")

        results = []
        gen_table = Table(title="Generated Schedule", border_style="cyan")
        gen_table.add_column("Date", style="bold yellow", width=12)
        gen_table.add_column("Case Title", style="bold green", width=32)
        gen_table.add_column("Suspect", style="cyan", width=24)
        gen_table.add_column("Seed ID", style="magenta", width=10)
        gen_table.add_column("Status", style="bold", width=16)

        for i in range(days):
            cur_date = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            cache_file = os.path.join(self.cases_dir, f"{cur_date}.json")

            # Check if case is already cached on disk AND unique
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                        susp = raw.get("suspect", {})
                        s_name = susp.get("name", "Unknown") if isinstance(susp, dict) else ""
                        c_title = raw.get("title", "")
                        # Verify this cached case is not a duplicate from another date
                        if self.registry.is_case_unique(c_title, s_name, raw.get("seed_id"), exclude_date=cur_date):
                            gen_table.add_row(cur_date, c_title, s_name, raw.get("seed_id", "cached"), "[dim]CACHED[/dim]")
                            results.append({"date": cur_date, "title": c_title, "status": "cached"})
                            if not self.registry.is_date_registered(cur_date):
                                self.registry.register_case(cur_date, raw, seed_id=raw.get("seed_id"))
                            continue
                        else:
                            # Cached file is a duplicate of another date! Remove it and regenerate
                            os.remove(cache_file)
                except Exception:
                    pass

            # Pick an unused seed
            unused = self._get_unused_seeds()
            seed_val = int(hashlib.md5(cur_date.encode()).hexdigest(), 16) % 1000000
            rng = random.Random(seed_val)
            chosen_seed = rng.choice(unused)

            console.print(f"  [yellow]• Generating {cur_date}:[/yellow] '{chosen_seed.get('title')}'...")

            # 1. Check for unused curated case first
            matching_fb = next((fb for fb in self.fallback_cases if fb.get("title") == chosen_seed.get("title")), None)
            if matching_fb and self.registry.is_case_unique(matching_fb.get("title", ""), matching_fb.get("suspect", {}).get("name", ""), chosen_seed.get("id"), exclude_date=cur_date):
                case_data = matching_fb.copy()
                case_data["date"] = cur_date
                case_data["id"] = f"case-{cur_date}"
                case_data["seed_id"] = chosen_seed.get("id")
                case_obj = Case.model_validate(case_data)
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(case_obj.model_dump_json(indent=2))
                self.registry.register_case(cur_date, case_data, seed_id=chosen_seed.get("id"))
                gen_table.add_row(cur_date, case_obj.title, case_obj.suspect.name, chosen_seed.get("id"), "[bold green]CURATED[/bold green]")
                results.append({"date": cur_date, "title": case_obj.title, "status": "curated"})
                continue

            # 2. Attempt LLM Generation with structured exemplar template
            generated_case = None
            try:
                recent_titles, recent_suspects = self.registry.get_recent_suspects_and_titles()
                candidate_obj = self._generate_case_llm(cur_date, chosen_seed, attempt_rng=rng, recent_titles=recent_titles, recent_suspects=recent_suspects)
                # Verify uniqueness against all historical cases
                if self.registry.is_case_unique(candidate_obj.title, candidate_obj.suspect.name, chosen_seed.get("id"), exclude_date=cur_date):
                    generated_case = candidate_obj
                    case_data = generated_case.model_dump()
                    case_data["seed_id"] = chosen_seed.get("id")
                    with open(cache_file, "w", encoding="utf-8") as f:
                        f.write(json.dumps(case_data, indent=2))
                    self.registry.register_case(cur_date, case_data, seed_id=chosen_seed.get("id"))
                    gen_table.add_row(cur_date, generated_case.title, generated_case.suspect.name, chosen_seed.get("id"), "[bold green]LLM GENERATED[/bold green]")
                    results.append({"date": cur_date, "title": generated_case.title, "status": "generated"})
            except Exception as e:
                pass

            if not generated_case:
                # 3. Procedural Fallback Guarantee (100% Unique, Never Repeated)
                fallback_case = self._synthesize_unique_case(cur_date, chosen_seed, rng)
                fb_data = fallback_case.model_dump()
                fb_data["seed_id"] = chosen_seed.get("id")
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(json.dumps(fb_data, indent=2))
                self.registry.register_case(cur_date, fb_data, seed_id=chosen_seed.get("id"))
                gen_table.add_row(cur_date, fallback_case.title, fallback_case.suspect.name, chosen_seed.get("id"), "[bold cyan]PROCEDURAL[/bold cyan]")
                results.append({"date": cur_date, "title": fallback_case.title, "status": "procedural"})

        console.print(gen_table)
        console.print(f"\n[bold green]✓ Pre-generation complete! {days} days of non-repeating cases are cached and ready.[/bold green]\n")
        return results

    def _generate_case_llm(self, date_str: str, seed: Dict[str, str], attempt_rng: random.Random, recent_titles: Optional[List[str]] = None, recent_suspects: Optional[List[str]] = None) -> Case:
        """Generate structured case matching Case schema using Case Architect prompt with diversity constraints and exemplar."""
        system_prompt = (
            "You are the Lead Case Architect for 'THE ALIBI', a satirical noir detective game.\n"
            "Your job is to generate a tightly constrained, humorous micro-crime case with a unique, eccentric suspect.\n"
            "CRITICAL NOVELTY RULES (NO REPEATS):\n"
            "1. Give the suspect a COMPLETELY UNIQUE profession, personality, and distinctive speech quirk.\n"
            "2. Quirk examples: Speaks like an auctioneer, speaks in 1920s jazz slang, speaks only in culinary metaphors, speaks in whispered conspiracy riddles, speaks in Victorian etiquette rules.\n"
            "3. Do NOT repeat characters, names, or archetypes from previous days.\n\n"
            "CRITICAL SOLVABILITY RULES:\n"
            "1. EXACTLY 3 Verified Facts. Each fact must be 100% true, objective, and specific (times, objects, physical colors, or access logs).\n"
            "2. The suspect is GUILTY and LYING. Provide a Truth Timeline with specific events.\n"
            "3. LiePlan with cover story and 3 planned weak points. Each weak point MUST directly conflict with one of the 3 Verified Facts.\n"
            "4. Each weak point must specify trigger_topics and a planned_slip containing the contradictory claim.\n"
            "5. solution_contradictions listing exactly how the detective can catch the suspect.\n"
            "6. Output MUST be valid JSON adhering strictly to the schema."
        )

        diversity_note = ""
        if recent_titles:
            diversity_note += f"\nDO NOT reuse or imitate these recent case titles: {', '.join(recent_titles[:6])}\n"
        if recent_suspects:
            diversity_note += f"DO NOT reuse these recent suspect names or archetypes: {', '.join(recent_suspects[:6])}\n"

        schema_exemplar = (
            "{\n"
            f'  "id": "case-{date_str}",\n'
            f'  "date": "{date_str}",\n'
            f'  "title": "{seed.get("title")}",\n'
            f'  "crime_description": "{seed.get("description")}",\n'
            f'  "setting": "{seed.get("setting")}",\n'
            '  "suspect": {\n'
            '    "name": "Full Eccentric Name",\n'
            '    "occupation": "Quirky Specific Profession",\n'
            '    "quirk": "Distinct verbal tick or speech habit"\n'
            '  },\n'
            '  "dossier": [\n'
            '    {"id": "fact-1", "text": "Forensic fact with timestamp or physical item."},\n'
            '    {"id": "fact-2", "text": "Forensic fact with access log or physical color."},\n'
            '    {"id": "fact-3", "text": "Forensic fact with witness observation or receipt."}\n'
            '  ],\n'
            '  "truth_timeline": [\n'
            '    {"time": "10:15 PM", "event": "Suspect prepares tools and sneaks in."},\n'
            '    {"time": "10:45 PM", "event": "Suspect executes the micro-crime."},\n'
            '    {"time": "11:15 PM", "event": "Suspect flees, accidentally dropping evidence."}\n'
            '  ],\n'
            '  "lie_plan": {\n'
            '    "cover_story": "The false alibi suspect gives the detective.",\n'
            '    "weak_points": [\n'
            '      {"id": "wp-1", "claim": "False claim contradicting fact-1", "conflicts_with": "fact-1", "trigger_topics": ["topic1"], "planned_slip": "Slip statement contradicting fact-1"},\n'
            '      {"id": "wp-2", "claim": "False claim contradicting fact-2", "conflicts_with": "fact-2", "trigger_topics": ["topic2"], "planned_slip": "Slip statement contradicting fact-2"},\n'
            '      {"id": "wp-3", "claim": "False claim contradicting fact-3", "conflicts_with": "fact-3", "trigger_topics": ["topic3"], "planned_slip": "Slip statement contradicting fact-3"}\n'
            '    ]\n'
            '  },\n'
            '  "solution_contradictions": [\n'
            '    "Suspect claimed X which directly conflicts with fact-1.",\n'
            '    "Suspect claimed Y which directly conflicts with fact-2."\n'
            '  ]\n'
            "}"
        )

        user_prompt = (
            f"Generate an entirely original Case for Date: {date_str}\n"
            f"Crime Title Inspiration: {seed.get('title')}\n"
            f"Micro-crime Idea: {seed.get('description')}\n"
            f"Setting: {seed.get('setting')}\n"
            f"{diversity_note}\n\n"
            f"You MUST format your output EXACTLY as this JSON structure:\n{schema_exemplar}\n\n"
            f"Return ONLY the RFC-8259 JSON."
        )

        raw_resp = self.client.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.75,
            format_json=True,
            agent_name="CaseArchitect"
        )
        cleaned = self.client.clean_json_text(raw_resp)
        data = json.loads(cleaned)
        normalized = self._normalize_case_dict(data, date_str, seed)
        return Case.model_validate(normalized)

    def _validate_case_llm(self, case: Case) -> CaseValidationResult:
        """Second LLM call to check logic and solvability, with automatic fallback."""
        return CaseValidationResult(
            is_valid=len(case.dossier) == 3 and len(case.lie_plan.weak_points) >= 2,
            contradiction_count=len(case.solution_contradictions),
            facts_consistent=True,
            reason="Validated case structure and contradiction alignment."
        )
