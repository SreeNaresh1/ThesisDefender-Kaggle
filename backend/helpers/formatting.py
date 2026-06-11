from models.schemas import ArgumentStructure, DefenseOutput, AttackOutput

def build_defense_user_prompt(
    argument: str,
    structure: ArgumentStructure
) -> str:
    assumptions_text = "\n".join([f"- {a}" for a in structure.assumptions]) if structure.assumptions else "None explicitly found."
    return f"""ORIGINAL ARGUMENT:
{argument}

MAIN CLAIM:
{structure.main_claim}

EXTRACTED ASSUMPTIONS:
{assumptions_text}

Generate the best possible defense for this argument."""

def build_prosecutor_user_prompt(
    argument: str,
    structure: ArgumentStructure,
    defense: DefenseOutput
) -> str:
    assumptions_text = "\n".join([f"- {a}" for a in structure.assumptions]) if structure.assumptions else "None explicitly found."
    defense_points = "\n".join([f"- {p}" for p in defense.supporting_points])
    return f"""ORIGINAL ARGUMENT:
{argument}

MAIN CLAIM:
{structure.main_claim}

EXTRACTED ASSUMPTIONS:
{assumptions_text}

STEEL-MANNED DEFENSE:
{defense.best_defense}

DEFENSE SUPPORTING POINTS:
{defense_points}

Generate the strongest counterargument by attacking the steel-manned defense and exposing logical gaps."""

def build_judge_user_prompt(
    argument: str,
    structure: ArgumentStructure,
    defense: DefenseOutput,
    attack: AttackOutput
) -> str:
    assumptions_text = "\n".join([f"- {a}" for a in structure.assumptions]) if structure.assumptions else "None explicitly found."
    return f"""ORIGINAL ARGUMENT:
{argument}

EXTRACTED ASSUMPTIONS:
{assumptions_text}

DEFENSE'S STRONGEST CASE:
{defense.best_defense}

PROSECUTOR'S ATTACK:
{attack.strongest_attack}

Evaluate the argument, assign a Resilience Score, identify the critical vulnerability, recommend fixes, and provide a stronger version of the original claim."""
