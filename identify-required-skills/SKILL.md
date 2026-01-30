---
name: identify-required-skills
description: Use when you have complex requirements or a large project context and need to identify the exact agent skills to use.
metadata:
  category: meta
  triggers: find relevant skills, analyze requirements, match skills, what skills to use, skill discovery, project setup
  references: python-pro, clean-code, writing-skills
---

# Identify Required Skills

> **Meta-Skill**: Analyzes requirements to recommend the perfect set of agent capabilities.

## When to Use

- **Starting a Project**: You have a list of requirements but don't know which tools/skills to use.
- **Complex Tasks**: The user asks "Can you help me build X?" and you need to staff the right abilities.
- **Skill Discovery**: You want to know if there's a specific skill for a detailed problem (e.g., "duplicate file finder").

## Capabilities

1. **Semantic Search**: Finds skills even if you don't use the exact name (e.g., "frontend" -> `react-best-practices`).
2. **Noise Filtering**: Ignores random chat text to focus on technical terms.
3. **Skill Bundling**: Automatically suggests related skills (e.g., Database -> Schema + Optimization).
4. **Report Generation**: Creates a `SKILLS_REQUIRED.md` with a quick-install command.

## Instructions

### 1. Run Analysis

Use the python script to analyze text or a file.

```bash
# Analyze a file
python .agent/skills/scripts/find_relevant_skills.py path/to/requirements.txt --report

# Analyze a raw string (use quotes)
python .agent/skills/scripts/find_relevant_skills.py "I need a React app with Python backend" --report
```

### 2. Review Recommendations

- **Core Matches**: The "Must Have" skills.
- **Bundle Recommendations**: logical additions to complete the stack.

### 3. Install & Activate

Copy the **Quick Install** command from the output report to load the skills into the workspace.

## Best Practices

- **Be Specific**: Inputting "web app" is vague. Inputting "Next.js dashboard with Supabase auth" yields precise results.
- **Use Reports**: Always use `--report` to give the user a tangible artifact (`SKILLS_REQUIRED.md`) they can read.
- **Don't Hallucinate**: Only recommend skills that actually exist in the `.agent/skills` directory.
