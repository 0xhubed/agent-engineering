## Creative Prompt Therapy — Forcing Novel Product Ideas on Existing Projects

> **Purpose:** This framework uses LLM prompt engineering to escape the "obvious improvement" attractor and generate genuinely novel ideas for *what your project could become* — not how the code should be written. The target is the **idea space**, not the architecture.

---

### Pre-Requisite: Feed the Problem Space

Before any phase, give the LLM deep context — but about the *problem and users*, not the code.

```
Here is my project: [name + one-sentence description]

Here is the problem it solves:
[What pain/need existed before this project? Who has it?]

Here is how it solves it today:
[The core user experience — what someone actually DOES with it]

Here is the implicit worldview / assumptions baked into the design:
[What does this project believe to be true about its domain?]

Here is who uses it and why they care:
[Target users + their actual motivation, not your intended one]

Here are the moments where users disengage, get bored, or wish it did more:
[Concrete friction in the EXPERIENCE, not in the code]
```

**Critical:** Include the *worldview and assumptions*, not just features. Novel product ideas come from challenging what the project takes for granted, not from adding more of what it already does.

---

### Phase 1 — Surface the Attractor (Map the Obvious)

```
Given this project, what are the 10 most obvious product improvements that
any product manager, competitor, or user would suggest? Think features,
integrations, UX improvements, and market expansions.

These are OFF LIMITS for the rest of this conversation — I already know
about them.

Label this list "THE BANNED LIST."
```

**Why:** You're extracting and quarantining the ideas that live in the statistical center of "what this product should do next." Every product roadmap is full of these. They're fine. They're also boring. By making the LLM say them first, you clear the path for everything that isn't on the default roadmap.

---

### Phase 2 — Forced-Domain Exploration

Pick ONE of these prompts (or run multiple in separate sessions):

#### Variant A — Alien Domain Transfer

```
You are now forbidden from thinking like a product manager, software
engineer, or anyone in the tech industry.

Analyze this project ONLY through the lens of [DOMAIN]. Use only
[DOMAIN] terminology and mental models. What does this perspective reveal
about what the product COULD be, what it's missing, or what problem it's
actually solving without knowing it?

Focus on the EXPERIENCE and the PROBLEM SPACE, not code structure.
Nothing from THE BANNED LIST. If you catch yourself suggesting a
conventional feature, stop and go weirder.
```

**High-value domain pairings by project type:**

| Project Type | Force These Domains |
|---|---|
| Trading / Finance tool | Epidemiology, Theater/live performance, Ecology, Swarm intelligence |
| Developer tool / CLI | Culinary arts, Choreography, Urban planning, Cartography |
| Data analysis platform | Investigative journalism, Archaeology, Musical composition |
| Social / Community app | Evolutionary biology, Theater improv, Urban sociology, Mycology |
| Productivity / Workflow | Restaurant kitchen operations, Air traffic control, Beehive management |
| Education / Learning | Apprenticeship guilds, Permaculture, Game level design |
| Content / Creative tool | Genetics, Architecture (buildings), Fermentation, Jazz improvisation |
| Marketplace / Platform | Coral reef ecology, Parliamentary procedure, Logistics networks |

#### Variant B — User Archetype Inversion

```
Describe 3 people who are NOT the intended user but who might discover
this project and try to use it for something you never imagined.

For each:
1. What would they be trying to accomplish?
2. What would they expect to exist that doesn't?
3. How would they "misuse" or repurpose the project in a creative way?

Now: which of these "misuses" reveal a genuine product capability that
SHOULD exist but doesn't? What latent value are they seeing that the
intended users are blind to?
```

#### Variant C — Failure Futurism

```
It's 3 years from now. This project succeeded — it has users, traction,
and reputation. But it just experienced a catastrophic RELEVANCE failure:
not a bug, but a shift in the world that made its core value proposition
obsolete. Users didn't leave because it broke. They left because the
problem it solves no longer matters.

Describe 3 such scenarios. For each:
1. What changed in the world?
2. What assumption did the project rely on that turned out to be fragile?
3. What could the project have evolved into BEFORE the shift happened
   that would have made it antifragile — actually benefiting from the
   change?
```

#### Variant D — Competitive Extinction

```
A competitor just killed this project's entire category. But they didn't
do it by building "a better version of the same thing" — they reframed
the problem so completely that users realized they'd been asking the
wrong question all along.

What question were users asking before? What question does the competitor
make them ask instead? What assumption about the problem space did the
competitor reject?

Now: can this project adopt that reframing? What would it become?
```

#### Variant E — The Adjacent Possible

```
This project sits at the intersection of several domains. Map the
neighboring problem spaces — not features to add, but entirely
different problems that could be solved by someone who already has
the context, data, relationships, or infrastructure this project creates.

What is the most surprising SECOND product that could emerge from this
project's foundation? Not a feature — a new product for a different
audience with a different value proposition that shares DNA with this one.
```

---

### Phase 3 — Novelty Scoring

```
Look at every idea you generated in Phase 2. For each, score:

1. DISTANCE (1-10): How far is this from THE BANNED LIST and from
   what any product manager would suggest for this category?
2. COHERENCE (1-10): Does this idea have internal logic? Could you
   pitch it to a smart skeptic and have them say "that's unusual
   but I see why it could work"?
3. IMPACT (1-10): If this worked, would it fundamentally change what
   the product IS or who it's for — or is it just a novel feature?
4. FEASIBILITY (1-10): Could a small team build a convincing prototype
   within a month?

Show the scores. Keep ONLY ideas where:
  Distance ≥ 7 AND Coherence ≥ 6 AND Impact ≥ 5

Kill everything else. If nothing survives, go back to Phase 2 with
a different domain. Don't lower the bar — find better ideas.
```

**Note:** FEASIBILITY is tracked but not used as a filter. A transformative idea that's hard to build is worth 10 easy features. You can figure out how to build it later.

---

### Phase 4 — Product Design Translation

```
For each surviving idea:

1. Describe the user experience. What does someone SEE and DO?
   Walk through it as a 60-second demo.
2. What's the "aha moment" — the point where a user goes from
   "interesting" to "I need this"?
3. Who is the user? Is it the same user as today, or a new audience?
4. What's the core mechanic that makes this work? Not the tech stack —
   the fundamental interaction or dynamic.
5. What existing capability of the project is the seed for this?
   What needs to change in the project's IDENTITY (not code) to
   accommodate it?
6. What's the cheapest possible prototype that tests whether the
   idea has legs? Not an MVP — a PROOF OF CONCEPT.
```

---

### Phase 5 — Adversarial Review

```
For each idea from Phase 4, respond as three different critics:

CRITIC 1 (The Reductionist): "Strip away the fancy metaphor. Isn't this
just [existing thing] with a new name? What's genuinely new about the
VALUE PROPOSITION, not the framing?"

CRITIC 2 (The Strategist): "Does this expand the project's moat or
dilute its identity? In 2 years, does this make the project more
focused or more confused?"

CRITIC 3 (The Target User): "Would I switch from what I use today?
Would I pay for this? Would I tell someone about it? What would I tell
them in one sentence?"

For any idea that survives all three critics with satisfying counters,
write a one-paragraph elevator pitch.
```

---

### Power Moves (Optional Amplifiers)

#### The Composition Trick
```
Take the top 2 surviving ideas. What happens if you merge them into
a single product concept? Sometimes two "good" ideas compose into one
"transformative" vision that neither achieves alone.
```

#### The Inversion Trick
```
What if you REMOVED the project's most central feature — the thing
everyone assumes IS the product? What's left? What does the project
become if it can no longer do the ONE THING it's known for?

Sometimes the most interesting product is hiding behind the obvious one.
```

#### The Scale Trick
```
What if this project had 1000x its current users/scope tomorrow?
Not "add servers" — what breaks CONCEPTUALLY? What assumption about
the problem space doesn't hold at scale? What new emergent behavior
appears when the system has that many participants/inputs/outputs?
```

#### The Time Travel Trick
```
Describe this project as it would exist in 1995, using only technology
available then. What's the core idea stripped of modern tooling?

Now: what would the 2030 version look like if current AI/tech trends
continue? Not "add AI" — what does the project become when its
underlying assumptions about what's possible change completely?
```

---

### Single-Prompt Compressed Version

For when you want quick results in one shot:

```
Here is my project: [context — problem, users, how it works, assumptions]

Do the following in sequence:

1. List the 10 most obvious product improvements. Label them BANNED —
   do not mention them again.

2. Analyze this project ONLY through the lens of [pick: epidemiology /
   theatrical production / ecology / urban planning / investigative
   journalism]. What does this perspective reveal about what the product
   COULD be? Generate 3 ideas. No tech/product jargon allowed. Focus
   on the experience and the problem space.

3. Score each idea:
   - Distance from BANNED list (1-10)
   - Internal coherence (1-10)
   - Potential impact on what the product IS (1-10)
   Keep only ideas scoring ≥7 / ≥6 / ≥5.

4. For survivors: describe the user experience as a 60-second demo.
   What's the "aha moment"? What's the cheapest proof of concept?

5. Attack the best idea: strip the metaphor — is this actually just
   [existing product/feature] in disguise? What's the real novelty?
   If it survives, write a one-paragraph elevator pitch.
```

---

### Example: Applying This to a Crypto Trading Agent Competition

**Context:** Agent Arena — a platform where AI agents compete in paper trading. Multiple LLMs, multiple architectures, same market data. Dashboard shows leaderboard and trades in real-time.

**Worldview/Assumptions:** The interesting question is which AI trades best. The user watches. Performance = P&L.

**Phase 1 BANNED LIST:** More indicators, better backtesting, risk management rules, more exchanges, better dashboard, persistent memory, parameter optimization, ELO rankings, multi-timeframe support, alert notifications.

**Phase 2 (Domain: Theater/Live Performance):**

"This competition has no dramatic arc — it's a flat timeline where numbers change. Every great performance has structure: tension, climax, release. What if competitions were *curated for drama*? Market conditions selected to create Act 1 (establishment), Act 2 (divergence), Act 3 (crisis). The observer agent becomes a narrator. And what if the audience isn't passive — what if spectators inject market events, becoming the market itself? The product transforms from 'benchmark dashboard' to 'interactive AI stress-test game.'"

**Phase 3:** Distance: 9. Coherence: 8. Impact: 9. ✓ Survives.

**Phase 4:** "A spectator opens Agent Arena and sees 6 AI agents trading. The market is calm — Act 1. Then the audience votes to inject a volatility spike. Agents scramble. The narrator (observer agent) builds tension: 'Claude is doubling down while GPT just panicked.' In the final act, a flash crash separates the survivors. The aha moment: the user realizes they're not watching a dashboard — they're playing a game where they stress-test AIs in real-time. Proof of concept: one button that injects a price shock into the simulated feed."

**Phase 5 Critic 1:** "This is just a trading simulator with drama." **Counter:** "Trading simulators simulate markets. This simulates *AI decision-making under pressure*, with the human as the antagonist. The product isn't the market — it's the AI behavior."
