"""
ThesisDefender MCP Tools — Pure Python Implementations
========================================================
This module contains the three tool implementations for the ThesisDefender
MCP server. All logic is self-contained: no external APIs, no databases,
no network calls. This makes them fast, deterministic, and offline-capable.

Tools
-----
  run_lookup_definition(term)       → LogicDefinition dict
  run_verify_claim_type(claim_text) → ClaimTypeAnalysis dict
  run_explain_research_term(term)   → ResearchTermExplanation dict

These functions are called by server.py via the @mcp.tool() decorator and
can also be called directly in tests without starting the MCP server.
"""

import re
from typing import Optional


# ===========================================================================
# TOOL 1 — Definition Lookup
# Knowledge base: logical, rhetorical, and argumentative terms
# ===========================================================================

DEFINITIONS: dict[str, dict] = {
    "steel man": {
        "term": "steel man",
        "definition": (
            "The practice of constructing the strongest possible version of an "
            "opposing argument before engaging with it. The opposite of a straw man. "
            "Forces the critic to grapple with the best form of a claim, not a weakened caricature."
        ),
        "category": "argumentation technique",
        "examples": [
            "Instead of 'Veganism is just a trend', steelman: 'Industrial animal agriculture causes measurable environmental harm at scale that individual dietary choices can meaningfully reduce.'",
            "Instead of 'AI safety concerns are overblown', steelman: 'Sufficiently capable AI systems optimizing proxy objectives could produce outcomes radically misaligned with human values in ways that are difficult to detect or reverse.'"
        ],
        "related_terms": ["straw man", "principle of charity", "charitable interpretation", "dialectic"]
    },
    "straw man": {
        "term": "straw man",
        "definition": (
            "A logical fallacy where someone misrepresents an opponent's argument "
            "to make it easier to attack, typically by exaggerating, oversimplifying, "
            "or distorting the original position."
        ),
        "category": "logical fallacy",
        "examples": [
            "Person A: 'We should have stricter gun regulations.' Person B attacks: 'So you want to ban all guns and leave people defenceless.'",
        ],
        "related_terms": ["steel man", "ad hominem", "false dichotomy", "red herring"]
    },
    "ad hominem": {
        "term": "ad hominem",
        "definition": (
            "A logical fallacy that attacks the character, motive, or other attribute "
            "of the person making the argument rather than addressing the argument itself."
        ),
        "category": "logical fallacy",
        "examples": [
            "Dismissing a climate scientist's findings because they once flew in a private jet.",
        ],
        "related_terms": ["tu quoque", "genetic fallacy", "appeal to authority"]
    },
    "post hoc": {
        "term": "post hoc",
        "definition": (
            "Post hoc ergo propter hoc ('after this, therefore because of this'). "
            "The fallacy of assuming that because one event preceded another, it caused it. "
            "Confuses temporal sequence with causation."
        ),
        "category": "logical fallacy",
        "examples": [
            "A rooster crows before sunrise; therefore the rooster causes the sun to rise.",
            "Crime dropped after the new policy; therefore the policy caused the drop."
        ],
        "related_terms": ["correlation vs causation", "causal fallacy", "confounding variable"]
    },
    "false dichotomy": {
        "term": "false dichotomy",
        "definition": (
            "Also called a false dilemma. Presents only two options as if they are the only "
            "possibilities, when in fact more options exist. Forces an artificial either/or choice."
        ),
        "category": "logical fallacy",
        "examples": [
            "'You're either with us or against us.'",
            "'Either we ban social media, or we accept that it destroys democracy.'"
        ],
        "related_terms": ["black-and-white thinking", "straw man", "excluded middle"]
    },
    "slippery slope": {
        "term": "slippery slope",
        "definition": (
            "Argues that one event will inevitably lead to an extreme outcome through a "
            "chain of events, without sufficient justification for why each step is inevitable. "
            "Can be valid if the chain is well-evidenced."
        ),
        "category": "logical fallacy",
        "examples": [
            "'If we allow marijuana, people will inevitably move on to heroin.'",
        ],
        "related_terms": ["causal chain", "reductio ad absurdum", "catastrophizing"]
    },
    "appeal to authority": {
        "term": "appeal to authority",
        "definition": (
            "Using an authority figure's endorsement as the primary evidence for a claim, "
            "especially when the authority lacks relevant expertise or when expert consensus differs. "
            "Not always a fallacy — citing legitimate experts is valid reasoning."
        ),
        "category": "logical fallacy",
        "examples": [
            "A celebrity endorsing a medical treatment without relevant qualifications.",
            "Citing a physicist on economics without acknowledging cross-domain limitations."
        ],
        "related_terms": ["ad hominem", "appeal to popularity", "expert consensus"]
    },
    "hasty generalization": {
        "term": "hasty generalization",
        "definition": (
            "Drawing a broad conclusion from an insufficient or unrepresentative sample. "
            "The sample size is too small, or the sample is biased, to support the conclusion."
        ),
        "category": "logical fallacy",
        "examples": [
            "Meeting two rude people from a country and concluding all people from that country are rude.",
        ],
        "related_terms": ["selection bias", "anecdotal evidence", "availability bias", "ecological fallacy"]
    },
    "burden of proof": {
        "term": "burden of proof",
        "definition": (
            "The obligation to provide evidence for a claim. In argumentation, "
            "whoever makes a positive claim bears the burden of proving it. "
            "The absence of counter-evidence is not proof of a claim."
        ),
        "category": "argumentation principle",
        "examples": [
            "If you claim a new drug works, you must provide evidence — the onus is not on critics to prove it does not work.",
        ],
        "related_terms": ["Hitchens's razor", "null hypothesis", "Occam's razor", "epistemic responsibility"]
    },
    "deductive reasoning": {
        "term": "deductive reasoning",
        "definition": (
            "Reasoning from general premises to a specific conclusion. "
            "If the premises are true and the argument is valid, the conclusion must be true. "
            "Moves from the general to the specific."
        ),
        "category": "reasoning type",
        "examples": [
            "All humans are mortal. Socrates is human. Therefore Socrates is mortal.",
        ],
        "related_terms": ["inductive reasoning", "syllogism", "modus ponens", "modus tollens"]
    },
    "inductive reasoning": {
        "term": "inductive reasoning",
        "definition": (
            "Reasoning from specific observations to a probable general conclusion. "
            "Unlike deduction, the conclusion is probable but not certain, even if all premises are true. "
            "Moves from the specific to the general."
        ),
        "category": "reasoning type",
        "examples": [
            "Every swan I have observed is white. Therefore, all swans are probably white. (Invalidated by black swans.)",
        ],
        "related_terms": ["deductive reasoning", "abductive reasoning", "hasty generalization", "falsifiability"]
    },
    "abductive reasoning": {
        "term": "abductive reasoning",
        "definition": (
            "Reasoning to the most plausible explanation for an observed phenomenon. "
            "Also called 'inference to the best explanation'. "
            "The conclusion is the simplest and most likely explanation, not necessarily the only one."
        ),
        "category": "reasoning type",
        "examples": [
            "The grass is wet — it probably rained (most likely explanation), though a sprinkler or dew are also possible.",
        ],
        "related_terms": ["Occam's razor", "hypothesis", "inductive reasoning", "parsimony"]
    },
    "modus ponens": {
        "term": "modus ponens",
        "definition": (
            "A valid deductive argument form: 'If P then Q. P is true. Therefore Q is true.' "
            "The most basic form of affirming the antecedent."
        ),
        "category": "formal logic",
        "examples": [
            "If it rains, the ground is wet. It is raining. Therefore the ground is wet.",
        ],
        "related_terms": ["modus tollens", "deductive reasoning", "syllogism", "affirming the consequent"]
    },
    "modus tollens": {
        "term": "modus tollens",
        "definition": (
            "A valid deductive argument form: 'If P then Q. Q is false. Therefore P is false.' "
            "Denying the consequent to deny the antecedent."
        ),
        "category": "formal logic",
        "examples": [
            "If it rains, the ground is wet. The ground is not wet. Therefore it did not rain.",
        ],
        "related_terms": ["modus ponens", "contrapositive", "denying the antecedent"]
    },
    "confirmation bias": {
        "term": "confirmation bias",
        "definition": (
            "The tendency to search for, favour, interpret, and remember information in a way "
            "that confirms one's preexisting beliefs or hypotheses. A cognitive bias affecting "
            "both individuals and researchers."
        ),
        "category": "cognitive bias",
        "examples": [
            "A researcher unconsciously designs a study to confirm their hypothesis.",
            "Only reading news sources that confirm existing political beliefs."
        ],
        "related_terms": ["cherry-picking", "selection bias", "motivated reasoning", "cognitive dissonance"]
    },
    "correlation vs causation": {
        "term": "correlation vs causation",
        "definition": (
            "Two variables may move together (correlation) without one causing the other. "
            "Correlation is a necessary but not sufficient condition for causation. "
            "Establishing causation requires ruling out confounding variables and reverse causation."
        ),
        "category": "causal reasoning",
        "examples": [
            "Ice cream sales and drowning rates both peak in summer — correlated, but ice cream does not cause drowning.",
        ],
        "related_terms": ["confounding variable", "post hoc", "causal mechanism", "randomized controlled trial"]
    },
    "confounding variable": {
        "term": "confounding variable",
        "definition": (
            "A variable that influences both the independent and dependent variable, "
            "creating a spurious association. Failing to account for confounders is a "
            "major source of invalid causal claims."
        ),
        "category": "research methodology",
        "examples": [
            "Age is a confounder in a study linking grey hair to heart disease — age causes both.",
        ],
        "related_terms": ["correlation vs causation", "control variable", "randomized controlled trial", "selection bias"]
    },
    "empirical evidence": {
        "term": "empirical evidence",
        "definition": (
            "Evidence obtained through observation, measurement, or experiment rather than "
            "pure reasoning. The foundation of scientific methodology. "
            "Contrasted with anecdotal evidence or a priori reasoning."
        ),
        "category": "epistemology",
        "examples": [
            "Clinical trial results, census data, telescope measurements, controlled experiments.",
        ],
        "related_terms": ["anecdotal evidence", "peer review", "replication", "falsifiability"]
    },
    "anecdotal evidence": {
        "term": "anecdotal evidence",
        "definition": (
            "Evidence based on personal accounts, individual cases, or isolated examples "
            "rather than systematic data collection. Can generate hypotheses but cannot "
            "establish statistical patterns or causal claims."
        ),
        "category": "epistemology",
        "examples": [
            "'My grandfather smoked his whole life and lived to 95' as evidence that smoking is safe.",
        ],
        "related_terms": ["empirical evidence", "hasty generalization", "selection bias", "availability bias"]
    },
    "occam's razor": {
        "term": "occam's razor",
        "definition": (
            "The principle that among competing explanations, the one with the fewest "
            "unnecessary assumptions should be preferred. 'Entities should not be multiplied "
            "beyond necessity.' A heuristic for choosing between theories of equal explanatory power."
        ),
        "category": "epistemology",
        "examples": [
            "If a patient has common symptoms, a common illness is more likely than a rare exotic disease.",
        ],
        "related_terms": ["parsimony", "abductive reasoning", "falsifiability", "Hitchens's razor"]
    },
    "reductio ad absurdum": {
        "term": "reductio ad absurdum",
        "definition": (
            "A logical technique that refutes an argument by showing that following it to "
            "its logical conclusion produces an absurd or contradictory result. "
            "Can be used validly in both formal logic and rhetoric."
        ),
        "category": "argumentation technique",
        "examples": [
            "If stealing is only wrong when it harms someone, and taking a single grain of rice from a warehouse harms no one, then by this logic, stealing entire warehouses grain-by-grain would be acceptable."
        ],
        "related_terms": ["slippery slope", "modus tollens", "logical contradiction"]
    },
    "circular reasoning": {
        "term": "circular reasoning",
        "definition": (
            "Also called begging the question (petitio principii). An argument where the "
            "conclusion is used as a premise, or where the truth of the conclusion is "
            "assumed in the premises. The argument is logically valid but epistemically empty."
        ),
        "category": "logical fallacy",
        "examples": [
            "'The Bible is true because it says so in the Bible.'",
            "'This is the best policy because no better policy exists.'"
        ],
        "related_terms": ["tautology", "petitio principii", "logical validity vs soundness"]
    },
    "false equivalence": {
        "term": "false equivalence",
        "definition": (
            "Treating two things as equal or equivalent when they are meaningfully different "
            "in kind, degree, or evidential support. Often appears in 'both sides' framing "
            "that equates a well-supported position with a fringe one."
        ),
        "category": "logical fallacy",
        "examples": [
            "Treating a peer-reviewed scientific consensus equally with a single industry-funded study.",
        ],
        "related_terms": ["false balance", "whataboutism", "bothsidesism", "false dichotomy"]
    },
    "scope condition": {
        "term": "scope condition",
        "definition": (
            "The specific circumstances, population, context, or range of cases within "
            "which a claim or theory is valid. A claim that is true under certain conditions "
            "may be false outside those conditions."
        ),
        "category": "argumentation",
        "examples": [
            "Comparative advantage as a principle of free trade applies under conditions of full employment and factor mobility that often do not hold.",
        ],
        "related_terms": ["ceteris paribus", "domain restriction", "generalizability", "external validity"]
    },
}


# ===========================================================================
# TOOL 2 — Claim Type Verification
# Heuristic analysis based on linguistic markers
# ===========================================================================

CLAIM_TYPE_CONFIG: dict[str, dict] = {
    "predictive": {
        "patterns": [
            r"\bwill\b", r"\bgoing to\b", r"\bforecast\b", r"\bpredict\b",
            r"\bby 20\d\d\b", r"\bexpect\b", r"\beventually\b", r"\bsoon\b",
            r"\bfuture\b", r"\bnext decade\b", r"\bin the coming\b",
        ],
        "attack_vectors": [
            "High uncertainty — future states depend on variables not yet measurable",
            "Historical counterexamples where similar predictions failed to materialize",
            "Current trends may not continue due to structural breaks or unforeseen disruptions",
            "Timeframe may be too vague or distant to constitute a falsifiable prediction",
        ],
        "scrutiny_questions": [
            "What specific mechanism drives this prediction?",
            "How has this type of prediction performed historically?",
            "What evidence would falsify this claim before the predicted date?",
        ],
    },
    "causal": {
        "patterns": [
            r"\bcause[sd]?\b", r"\bleads? to\b", r"\bresults? in\b",
            r"\bbecause of\b", r"\bdue to\b", r"\bdriven by\b",
            r"\bresponsible for\b", r"\bproduce[sd]?\b", r"\btrigger\b",
            r"\bgenerate[sd]?\b",
        ],
        "attack_vectors": [
            "Correlation without causation — the relationship may be coincidental or spurious",
            "Confounding variables not accounted for that explain both the cause and effect",
            "Reverse causation — the assumed effect may independently influence the cause",
            "Selection bias in the evidence base used to establish the causal claim",
        ],
        "scrutiny_questions": [
            "What is the proposed causal mechanism step-by-step?",
            "Have confounding variables been identified and controlled for?",
            "Does this correlation hold across different populations, time periods, or contexts?",
        ],
    },
    "factual": {
        "patterns": [
            r"\bproven\b", r"\bshows?\b", r"\bdemonstrates?\b", r"\bfacts?\b",
            r"\bresearch\b", r"\bstudies?\b", r"\bdata\b", r"\bevidence\b",
            r"\bstatistic\w*\b", r"\bmeasured\b", r"\bdocumented\b",
        ],
        "attack_vectors": [
            "Data quality and representativeness of the underlying research sample",
            "Methodological flaws — insufficient controls, small sample size, lack of replication",
            "Outdated evidence that no longer reflects current conditions or scientific consensus",
            "Cherry-picking confirming evidence while ignoring contradictory or null findings",
        ],
        "scrutiny_questions": [
            "What is the source, quality, and recency of the primary evidence?",
            "Has this finding been independently replicated?",
            "Is the cited evidence peer-reviewed and is the journal reputable?",
        ],
    },
    "ethical": {
        "patterns": [
            r"\bshould\b", r"\bought to\b", r"\bmoral\b", r"\bright\b",
            r"\bwrong\b", r"\bethical\b", r"\bduty\b", r"\bobligation\b",
            r"\bjust\b", r"\bfair\b", r"\bjustified\b", r"\bunjust\b",
        ],
        "attack_vectors": [
            "Moral framework dependency — conclusion changes under different ethical systems (utilitarian vs deontological)",
            "Value pluralism — reasonable people disagree on the underlying foundational values",
            "Is-ought fallacy — descriptive facts alone cannot logically justify prescriptive moral conclusions",
            "Scope of harm or benefit may be systematically underestimated or overestimated",
        ],
        "scrutiny_questions": [
            "Which ethical framework does this argument depend on and is it the only valid one?",
            "Are there competing legitimate values or rights being ignored or discounted?",
            "What are the second-order moral consequences of acting on this claim?",
        ],
    },
    "policy": {
        "patterns": [
            r"\blaw\b", r"\bpolicy\b", r"\bgovernment\b", r"\bregulat\w*\b",
            r"\bban\b", r"\bmandate\b", r"\blegislat\w*\b", r"\btax\b",
            r"\bsubsid\w*\b", r"\breform\b", r"\bincentiv\w*\b",
        ],
        "attack_vectors": [
            "Implementation challenges and unintended second-order consequences at scale",
            "Enforcement feasibility and compliance costs disproportionately borne by affected parties",
            "Alternative policies that achieve the same objective with fewer trade-offs or side effects",
            "Distributional effects — who disproportionately bears the costs versus receiving the benefits",
        ],
        "scrutiny_questions": [
            "How would this policy be enforced in practice and what are the compliance costs?",
            "What are the projected second-order effects and who bears them?",
            "What alternatives were considered and why were they rejected?",
        ],
    },
    "subjective": {
        "patterns": [
            r"\bI think\b", r"\bI believe\b", r"\bI feel\b",
            r"\bin my opinion\b", r"\bseems\b", r"\bappears\b",
            r"\bfeel like\b", r"\bsense that\b", r"\bin my experience\b",
        ],
        "attack_vectors": [
            "Lack of objective, verifiable evidence — rests entirely on personal perception or anecdote",
            "Availability bias — memorable personal examples may not be statistically representative",
            "Overgeneralization from limited personal experience to a universal or group-level claim",
            "Absence of clear falsification criteria makes the claim unfalsifiable in principle",
        ],
        "scrutiny_questions": [
            "What objective evidence supports this beyond personal experience?",
            "How representative is this individual's experience of the broader population?",
            "How would this claim be proven wrong — is there any evidence that could do so?",
        ],
    },
}

_DEFAULT_CLAIM_TYPE = "factual"


# ===========================================================================
# TOOL 3 — Research Term Explanation
# Knowledge base: methodology, statistics, and research design
# ===========================================================================

RESEARCH_TERMS: dict[str, dict] = {
    "peer review": {
        "term": "peer review",
        "field": "research methodology",
        "explanation": (
            "A quality-control process where a researcher's work is evaluated by "
            "independent experts in the same field before publication. Identifies "
            "methodological errors, unsupported claims, and logical gaps. "
            "Peer review is a filter, not a guarantee of correctness."
        ),
        "common_misconceptions": [
            "Peer-reviewed means definitely true — it means qualified experts found no major flaws at submission time.",
            "Peer review catches all errors — replication crises show that flawed studies can pass review.",
        ],
        "example_in_context": "A peer-reviewed study on vaccine efficacy has been vetted by independent immunologists, making it more reliable than a preprint or press release.",
    },
    "meta-analysis": {
        "term": "meta-analysis",
        "field": "statistics / research methodology",
        "explanation": (
            "A statistical technique that combines results from multiple independent studies "
            "on the same topic to produce a more precise overall estimate of an effect. "
            "More powerful than any single study, but susceptible to publication bias "
            "if only published (positive-result) studies are included."
        ),
        "common_misconceptions": [
            "Meta-analysis always gives the definitive answer — garbage in, garbage out applies.",
            "More studies in the meta-analysis always means more accurate — low-quality studies still dilute results.",
        ],
        "example_in_context": "A meta-analysis of 50 RCTs on a drug gives a much more reliable efficacy estimate than any single trial alone.",
    },
    "randomized controlled trial": {
        "term": "randomized controlled trial",
        "field": "experimental research / medicine",
        "explanation": (
            "A study design where participants are randomly assigned to treatment or control groups. "
            "Random assignment controls for both known and unknown confounders, making RCTs the "
            "gold standard for establishing causal relationships. "
            "Still limited by generalizability to real-world populations."
        ),
        "common_misconceptions": [
            "RCTs always prove causation — external validity (generalizability) is a separate question.",
            "All RCTs are equally good — blinding, allocation concealment, and attrition matter enormously.",
        ],
        "example_in_context": "An RCT on a new medication randomly assigns patients to drug or placebo, controlling for selection bias that would exist in an observational study.",
    },
    "p-value": {
        "term": "p-value",
        "field": "statistics",
        "explanation": (
            "The probability of observing results at least as extreme as those obtained, "
            "assuming the null hypothesis is true. A p-value below 0.05 is conventionally "
            "called 'statistically significant' but this threshold is arbitrary. "
            "P-values do not measure effect size, practical importance, or the probability "
            "that the hypothesis is true."
        ),
        "common_misconceptions": [
            "p < 0.05 means the result is practically important — a tiny effect can be statistically significant with a large sample.",
            "p < 0.05 means there is a 95% chance the result is real — this is a common misinterpretation.",
        ],
        "example_in_context": "A drug showing p=0.001 improvement in blood pressure may be statistically significant but a 0.1 mmHg change has no clinical relevance.",
    },
    "statistical significance": {
        "term": "statistical significance",
        "field": "statistics",
        "explanation": (
            "A result is statistically significant if it is unlikely to have occurred by chance "
            "under the null hypothesis (typically p < 0.05). Widely used but also widely criticized "
            "for encouraging binary thinking about continuous evidence. "
            "Should always be reported alongside effect size and confidence intervals."
        ),
        "common_misconceptions": [
            "Statistical significance equals real-world importance — they are independent concepts.",
            "Non-significant results mean no effect exists — they may mean insufficient power to detect a real effect.",
        ],
        "example_in_context": "A study with 10,000 participants may detect a statistically significant difference that is too small to matter in practice.",
    },
    "effect size": {
        "term": "effect size",
        "field": "statistics",
        "explanation": (
            "A quantitative measure of the magnitude of an experimental effect, "
            "independent of sample size. Common measures include Cohen's d (for means), "
            "r (for correlations), and odds ratios. "
            "Essential context for interpreting whether a statistically significant result matters."
        ),
        "common_misconceptions": [
            "A large p-value means a large effect — these are independent; sample size drives p-values.",
        ],
        "example_in_context": "Cohen's d = 0.2 is small, d = 0.5 is medium, d = 0.8 is large. A drug with d = 0.1 may be significant but rarely worth using.",
    },
    "confidence interval": {
        "term": "confidence interval",
        "field": "statistics",
        "explanation": (
            "A range of values calculated from sample data that, if the sampling procedure "
            "were repeated many times, would contain the true population parameter a specified "
            "percentage of the time (e.g., 95%). Wider intervals indicate more uncertainty. "
            "Should be reported alongside point estimates."
        ),
        "common_misconceptions": [
            "A 95% CI means there's a 95% probability the true value is in this specific interval — frequentist CIs don't work that way.",
            "Non-overlapping CIs always mean statistical significance — not necessarily true for individual CIs.",
        ],
        "example_in_context": "A drug efficacy estimate of 30% (95% CI: 10%–50%) indicates substantial uncertainty about the true effect.",
    },
    "observational study": {
        "term": "observational study",
        "field": "research methodology",
        "explanation": (
            "A study where the researcher observes subjects without any intervention or "
            "random assignment. Useful for establishing associations and generating hypotheses, "
            "but cannot establish causation as reliably as an RCT due to confounding variables "
            "and selection bias."
        ),
        "common_misconceptions": [
            "A large observational study is as reliable as an RCT — the absence of randomization is a fundamental limitation.",
        ],
        "example_in_context": "Linking coffee consumption to reduced Parkinson's risk via observational data raises causation questions — coffee drinkers may differ systematically from non-drinkers.",
    },
    "null hypothesis": {
        "term": "null hypothesis",
        "field": "statistics / scientific method",
        "explanation": (
            "The default assumption that there is no effect, no difference, or no relationship "
            "between variables. Statistical tests attempt to reject the null hypothesis. "
            "Failing to reject it does not prove the null is true — only that the evidence "
            "was insufficient to reject it at the chosen significance level."
        ),
        "common_misconceptions": [
            "Failing to reject the null proves the null is true — absence of evidence is not evidence of absence.",
        ],
        "example_in_context": "The null hypothesis for a drug trial is 'the drug has no effect on the outcome.' Rejecting it with p<0.05 suggests (but doesn't prove) the drug works.",
    },
    "selection bias": {
        "term": "selection bias",
        "field": "research methodology",
        "explanation": (
            "A bias that arises when the sample used is not representative of the target "
            "population, often because the selection mechanism is correlated with the "
            "outcome of interest. Undermines the generalizability of findings."
        ),
        "common_misconceptions": [
            "A large sample eliminates selection bias — a large biased sample is still biased.",
        ],
        "example_in_context": "Studying health outcomes only in people who volunteer for a health study — healthier people self-select in, biasing results upward.",
    },
    "replication crisis": {
        "term": "replication crisis",
        "field": "philosophy of science / research methodology",
        "explanation": (
            "The ongoing finding that many published scientific results, especially in "
            "psychology, medicine, and social science, fail to replicate in subsequent "
            "independent studies. Caused by publication bias, p-hacking, HARKing, "
            "and underpowered studies."
        ),
        "common_misconceptions": [
            "Only social science has a replication crisis — it affects medicine, nutrition, economics, and other fields.",
        ],
        "example_in_context": "The Open Science Collaboration found that only ~39% of psychology studies successfully replicated when rerun by independent labs.",
    },
    "external validity": {
        "term": "external validity",
        "field": "research methodology",
        "explanation": (
            "The degree to which study results can be generalized beyond the specific "
            "sample, setting, time, and conditions of the study. High internal validity "
            "(e.g., from an RCT) does not guarantee high external validity."
        ),
        "common_misconceptions": [
            "A rigorous RCT automatically generalizes to all populations — the study sample may be highly specific.",
        ],
        "example_in_context": "A drug trial conducted only on 30–50 year old men in the US may not generalize to elderly women in different healthcare systems.",
    },
}


# ===========================================================================
# Public tool runner functions (called by server.py @mcp.tool handlers)
# ===========================================================================

def run_lookup_definition(term: str) -> dict:
    """
    Look up a logical, rhetorical, or argumentative term.

    Search priority:
      1. Exact match (case-insensitive)
      2. Substring match (term found in any key or key found in term)
      3. Returns a 'not found' result with available term list

    Args:
        term: The term to look up (e.g., "steel man", "ad hominem").

    Returns:
        dict with keys: term, definition, category, examples, related_terms
    """
    normalized = term.lower().strip()

    # 1. Exact match
    if normalized in DEFINITIONS:
        return DEFINITIONS[normalized]

    # 2. Partial / substring match
    for key, entry in DEFINITIONS.items():
        if normalized in key or key in normalized:
            return entry

    # 3. Not found
    return {
        "term": term,
        "definition": f"'{term}' was not found in the ThesisDefender definition knowledge base.",
        "category": "unknown",
        "examples": [],
        "related_terms": [],
        "available_terms": sorted(DEFINITIONS.keys()),
    }


def run_verify_claim_type(claim_text: str) -> dict:
    """
    Heuristically identify the logical type of a claim and return
    targeted attack vectors for that claim type.

    The analysis is based on linguistic marker patterns. It assigns
    a confidence score based on the density of matching markers.

    Args:
        claim_text: The main claim text to analyse.

    Returns:
        dict with keys: claim_type, confidence, markers_found,
                        typical_attack_vectors, scrutiny_questions,
                        claim_preview
    """
    text_lower = claim_text.lower()
    scores: dict[str, int] = {}

    for ctype, config in CLAIM_TYPE_CONFIG.items():
        matches = sum(
            1 for pattern in config["patterns"]
            if re.search(pattern, text_lower)
        )
        scores[ctype] = matches

    best_type = max(scores, key=lambda t: scores[t])
    best_score = scores[best_type]
    n_patterns = len(CLAIM_TYPE_CONFIG[best_type]["patterns"])

    # Confidence: base 0.30 when no markers found, up to 0.95 when most match
    if best_score == 0:
        confidence = 0.30
        best_type = _DEFAULT_CLAIM_TYPE
    else:
        confidence = round(min(0.40 + (best_score / n_patterns) * 0.55, 0.95), 2)

    config = CLAIM_TYPE_CONFIG[best_type]

    return {
        "claim_type": best_type,
        "confidence": confidence,
        "markers_found": [
            p for p in config["patterns"]
            if re.search(p, text_lower)
        ],
        "typical_attack_vectors": config["attack_vectors"],
        "scrutiny_questions": config["scrutiny_questions"],
        "claim_preview": claim_text[:200] + ("…" if len(claim_text) > 200 else ""),
    }


def run_explain_research_term(term: str) -> dict:
    """
    Explain a research methodology or statistics term.

    Args:
        term: The research term to explain (e.g., "p-value", "meta-analysis").

    Returns:
        dict with keys: term, field, explanation,
                        common_misconceptions, example_in_context
    """
    normalized = term.lower().strip()

    # 1. Exact match
    if normalized in RESEARCH_TERMS:
        return RESEARCH_TERMS[normalized]

    # 2. Substring match
    for key, entry in RESEARCH_TERMS.items():
        if normalized in key or key in normalized:
            return entry

    # 3. Not found
    return {
        "term": term,
        "field": "unknown",
        "explanation": f"'{term}' was not found in the research methodology knowledge base.",
        "common_misconceptions": [],
        "example_in_context": "",
        "available_terms": sorted(RESEARCH_TERMS.keys()),
    }
