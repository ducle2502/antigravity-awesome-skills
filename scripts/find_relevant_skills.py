#!/usr/bin/env python3
"""
Find Relevant Skills Script
===========================

Analyzes input text (requirements, tech stacks) to identify relevant agent skills.
Adheres to Clean Code principles: SRP, specific naming, and type safety.

Usage:
    python find_relevant_skills.py <input_source> [--top N] [--report]
"""

import argparse
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass

try:
    from rapidfuzz import fuzz, utils
except ImportError:
    print("Error: rapidfuzz is required. Please 'pip install rapidfuzz'")
    sys.exit(1)

# --- Types & Constants ---

@dataclass
class Skill:
    name: str
    description: str
    tags: str
    triggers: str
    full_text: str

@dataclass
class Bundle:
    name: str
    description: str
    skills: List[str]

@dataclass
class SearchResult:
    skill: Skill
    score: float

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILLS_ROOT = SCRIPT_DIR.parent
CATALOG_PATH = SKILLS_ROOT / "CATALOG.md"
BUNDLES_PATH = SKILLS_ROOT / "docs" / "BUNDLES.md"

NOISE_THRESHOLD = 55.0
HIGH_CONFIDENCE = 75.0

# --- 1. Data Loading (DAL) ---

def load_catalog_skills() -> List[Skill]:
    """Parses the CATALOG.md file into Skill objects."""
    if not CATALOG_PATH.exists():
        print(f"Error: Catalog not found at {CATALOG_PATH}")
        sys.exit(1)

    skills: List[Skill] = []
    with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        if not line.strip().startswith('|'):
            continue
        
        parts = [p.strip() for p in line.split('|')]
        # Expected: | `name` | description | tags | triggers |
        if len(parts) < 5:
            continue
            
        name = parts[1].replace('`', '').strip()
        if name == "Skill" or "---" in name:
            continue
            
        skills.append(Skill(
            name=name,
            description=parts[2],
            tags=parts[3],
            triggers=parts[4],
            full_text=f"{name} {parts[2]} {parts[3]} {parts[4]}"
        ))
    return skills


def load_skill_bundles() -> Dict[str, Bundle]:
    """Parses BUNDLES.md into Bundle objects."""
    bundles: Dict[str, Bundle] = {}
    if not BUNDLES_PATH.exists():
        return bundles

    current_bundle: Optional[Bundle] = None
    with open(BUNDLES_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("## "):
                name = line.replace("## ", "").strip()
                current_bundle = Bundle(name=name, description="", skills=[])
                bundles[name] = current_bundle
            elif line.startswith("- `") and current_bundle:
                skill_name = line.split("`")[1]
                current_bundle.skills.append(skill_name)
            elif current_bundle and line and not line.startswith("-") and not line.startswith("#"):
                current_bundle.description += line + " "

    return bundles

# --- 2. Input Processing ---

def get_clean_input_text(source: str) -> str:
    """Reads file or returns raw string, then cleans markdown."""
    text = source
    path = Path(source)
    
    # Heuristic: If it looks like a file path and exists, read it
    valid_path_chars = set(source) - set("?*<>|\"")
    if len(valid_path_chars) == len(source):
        try:
            if path.exists() and path.is_file():
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
        except OSError:
            pass # Treat as text

    # Remove markdown links
    return re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)


def extract_search_entities(text: str) -> List[str]:
    """Splits text into search entities using common delimiters."""
    # Normalize delimiters to newlines
    for char in [',', ';', '•', '-']:
        text = text.replace(char, '\n')
    
    entities = [line.strip() for line in text.split('\n') if line.strip()]
    return list(set(entities)) # Unique

# --- 3. Core Logic (Business Rules) ---

def calculate_relevance(query: str, skill: Skill) -> float:
    """Calculates weighted similarity score."""
    q = utils.default_process(query)
    name_score = fuzz.partial_ratio(q, skill.name)
    trigger_score = fuzz.token_set_ratio(q, skill.triggers)
    text_score = fuzz.token_set_ratio(q, skill.full_text)
    
    # 40% Name, 40% Trigger, 20% Context
    return (name_score * 0.4) + (trigger_score * 0.4) + (text_score * 0.2)


def filter_valid_entities(entities: List[str], skills: List[Skill]) -> List[str]:
    """Keeps entities that match at least one skill above threshold."""
    valid = []
    for entity in entities:
        # Check against all skills to find max possible score
        max_score = max(calculate_relevance(entity, s) for s in skills) if skills else 0
        if max_score >= NOISE_THRESHOLD:
            valid.append(entity)
    return valid


def search_skills(entities: List[str], skills: List[Skill], top_n: int) -> Dict[str, List[SearchResult]]:
    """Performs fuzzy search for each entity."""
    results = {}
    for entity in entities:
        matches = [
            SearchResult(skill, calculate_relevance(entity, skill)) 
            for skill in skills
        ]
        # Sort desc by score
        matches.sort(key=lambda x: x.score, reverse=True)
        results[entity] = matches[:top_n]
    return results


def find_bundled_skills(results: Dict[str, List[SearchResult]], bundles: Dict[str, Bundle]) -> Set[str]:
    """Finds related skills from bundles based on high-confidence matches."""
    found_names = {
        scan.skill.name 
        for matches in results.values() 
        for scan in matches 
        if scan.score > 65.0
    }
    
    extras = set()
    for bundle in bundles.values():
        bundle_skills = set(bundle.skills)
        if found_names.intersection(bundle_skills):
            extras.update(bundle_skills - found_names)
            
    return extras

# --- 4. Presentation (View) ---

def generate_report_content(
    results: Dict[str, List[SearchResult]], 
    extras: Set[str], 
    all_skills: List[Skill]
) -> str:
    """Generates the Markdown report content."""
    
    skill_map = {s.name: s for s in all_skills}
    
    # Identify Core vs Recommended
    core_skills = set()
    for matches in results.values():
        for scan in matches:
            if scan.score > HIGH_CONFIDENCE:
                core_skills.add(scan.skill.name)

    recommended_skills = sorted(list(core_skills.union(extras)))
    
    # Build MD
    md = [
        "# Skill Implementation Report\n",
        "**Based on analysis of your requirements.**\n",
        "## 1. Required Skills\n",
        "### CORE MATCHES (High Relevance)"
    ]
    
    for name in sorted(list(core_skills)):
        s = skill_map.get(name)
        if s: md.append(f"- **{name}**: {s.description}")

    md.append("\n### RECOMMENDED (Bundles & Ecosystem)")
    for name in extras:
        s = skill_map.get(name)
        if s: md.append(f"- **{name}**: {s.description}")

    # Install Command
    md.append("\n## 2. Quick Install\n")
    md.append("Run this command to install the skills:")
    md.append("```powershell")
    
    cmd = "# PowerShell\n"
    for name in recommended_skills:
        cmd += f"Copy-Item -Recurse -Force '.agent/skills/skills/{name}' .agent/skills/skills/\n"
    md.append(cmd)
    md.append("```\n")
    
    return "\n".join(md)


def print_console_summary(results: Dict[str, List[SearchResult]], extras: Set[str]):
    """Prints a concise summary to stdout."""
    print("\nSearch Results:")
    print("=" * 60)
    
    for entity, matches in results.items():
        if not matches: continue
        top_score = matches[0].score
        if top_score < NOISE_THRESHOLD: continue
        
        print(f"\nQuery: '{entity}'")
        for match in matches:
            # Filter tail
            if match.score < NOISE_THRESHOLD or match.score < (top_score - 20):
                continue
            print(f"  [{match.score:.0f}%] {match.skill.name}")
            
    if extras:
        print("\n(+) Bundle Recommendations:")
        for name in sorted(list(extras)):
            print(f"  - {name}")

# --- 5. Main ---

def main():
    parser = argparse.ArgumentParser(description="Find relevant agent skills (Clean Code Version)")
    parser.add_argument("input_source", help="File path or text string")
    parser.add_argument("--top", type=int, default=5, help="Top N results per entity")
    parser.add_argument("--report", action="store_true", help="Generate SKILLS_REQUIRED.md")
    
    args = parser.parse_args()
    
    # Load
    skills = load_catalog_skills()
    bundles = load_skill_bundles()
    
    # Process
    raw_text = get_clean_input_text(args.input_source)
    entities = extract_search_entities(raw_text)
    
    # Filter
    valid_entities = filter_valid_entities(entities, skills)
    if not valid_entities:
        print("No valid technical terms found in input.")
        return

    # Search
    print(f"Analyzing {len(valid_entities)} valid entities...")
    results = search_skills(valid_entities, skills, args.top)
    
    # Bundle
    extras = find_bundled_skills(results, bundles)
    
    # Output
    print_console_summary(results, extras)
    
    if args.report:
        report = generate_report_content(results, extras, skills)
        out_path = Path("SKILLS_REQUIRED.md")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n[SUCCESS] Report generated: {out_path.absolute()}")

if __name__ == "__main__":
    main()
