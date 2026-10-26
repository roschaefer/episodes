---
title: "A reference implementation"
description: "What matters is how splicing should behave in each workflow; the reference implementation shows that the specification can be built."
topics: [git, testing]
question: "Do you write down how your tool should behave before you build it?"
docs: ../git-splice/test/scenarios/README.md
---

git-splice is a tool, but the tool isn't what I care about. I care about the workflows: how should splicing behave when I work on a branch, when a pull request gets squash-merged, or when someone rewrites the other repository's history?

## Scenarios

For each of these situations, I write a scenario: a small example with a state before, a command, and the state after. In it, I decide how a tool *should* behave. Together, the scenarios are the specification:

```text
test/scenarios/
├── 01-everyday-sync/
├── 02-starting-a-splice/
├── 03-branches-and-teamwork/
├── 04-upstreams/
├── 05-nested-splices/
├── 06-rewritten-history/
└── 07-moved-folders/
```

You can read them all here:

```text
https://roschaefer.github.io/git-splice/test/scenarios/
```

## Why build it, then?

The specification doesn't depend on Git. A tool for Sapling or Jujutsu that behaves as the scenarios say would splice just as well.

That I write the reference implementation at the same time shows that the specification can be built. And it keeps the specification honest: a scenario that no tool can fulfil shows up right away.

How a scenario checks itself, I'll show in the next episode.
