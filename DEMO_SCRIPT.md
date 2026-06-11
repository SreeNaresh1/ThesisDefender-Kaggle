# ThesisDefender Demo Script
**Time:** 2-3 minutes
**Target Argument:** "Artificial intelligence will replace the majority of software engineering jobs within the next 10 years."

### [0:00\u20130:15] HOOK
**[Screen]**: Empty ThesisDefender input page
**Say**: "Every argument has a weakest link \u2014 one assumption that, if challenged, collapses everything else. Most people never find it. ThesisDefender finds it in 20 seconds."

### [0:15\u20130:30] INPUT
**[Screen]**: Type argument into textarea
**Say**: "Here's a claim you've definitely heard: AI will replace most software engineers in the next 10 years. Strong claim. Lots of people believe it. Let's stress-test it."
**[Screen]**: Click Analyze Argument

### [0:30\u20130:55] PROCESSING
**[Screen]**: ProgressSection \u2014 step 1 activates
**Say**: "ThesisDefender runs 3 reasoning steps. First, it structures the argument \u2014 extracts the core claim, the sub-claims, and the implicit assumptions the argument requires to be true."
**[Screen]**: Step 1 \u2192 Step 2 (retrieving + reasoning)
**Say**: "Then it retrieves real evidence via Microsoft's Foundry IQ \u2014 the agentic retrieval layer that reasons about where to search and what to look for. It uses that evidence to build the strongest possible defense and the strongest possible attack. Simultaneously. One reasoning pass."
**[Screen]**: Step 3 activates
**Say**: "Finally, it delivers a verdict."

### [0:55\u20131:15] RESILIENCE SCORE
**[Screen]**: Results animate in \u2014 meter marker slides to ~41
**Say**: "Resilience Score: 41 out of 100. Mixed evidence. The argument has a valid core but significant exploitable weaknesses. Let's see what that means."

### [1:15\u20131:45] DEFENSE AND ATTACK
**[Screen]**: Highlight SteelManPanel
**Say**: "The defense is actually strong. GitHub Copilot productivity data, code generation benchmarks, and clear economic incentives all support this argument."
**[Screen]**: Highlight AttackPanel
**Say**: "But the attack is stronger. The argument conflates automation of specific tasks with replacement of the role. It ignores accountability \u2014 who is liable when AI-generated code fails in production? And tacit knowledge \u2014 the judgment calls that never make it into training data."

### [1:45\u20132:10] WEAKEST LINK
**[Screen]**: WeakestLinkPanel \u2014 prominent
**Say**: "Here's the keystone. The weakest link is the word 'replace'. The argument treats augmentation and displacement as identical. If 'replace' means 'handle all the same tasks', it's demonstrably false today. If it means 'reduce headcount', it may be true in some organizations but not others. Until this is defined, the entire argument is unfalsifiable."
**[Screen]**: StrengthPanel
**Say**: "ThesisDefender rewrites the claim with this patched: 'AI will automate the majority of routine software engineering tasks within 10 years, significantly reducing the number of junior engineers required for maintenance and feature work.' That's a defensible claim. The original one isn't."

### [2:10\u20132:35] IMPROVEMENTS
**[Screen]**: ImprovementsPanel
**Say**: "Three specific improvements. Define 'replace' precisely. Scope the claim to specific engineering roles rather than all software engineers. Add a measurable threshold \u2014 'majority' needs a number."
**[Screen]**: Scroll to evidence panel, open it
**Say**: "Every conclusion is grounded in sources retrieved by Foundry IQ. 8 sources. Agentic multi-hop retrieval. Nothing is hallucinated \u2014 the evidence trail is right here."

### [2:35\u20132:50] TECHNICAL CLOSE
**[Screen]**: ProgressSection replay \u2014 3 steps
**Say**: "Three LLM calls. One text input. Under 25 seconds. Built on Microsoft AI Foundry with Foundry IQ as the intelligence layer. The reasoning is transparent, grounded, and reproducible."

### [2:50\u20133:00] CLOSE
**[Screen]**: Input box, empty, ready
**Say**: "ThesisDefender doesn't win your argument for you. It finds the hole in it \u2014 before someone else does."
**[Screen]**: GitHub URL
