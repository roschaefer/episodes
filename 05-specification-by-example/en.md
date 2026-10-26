---
title: "Specification by example"
description: "What matters is how splicing should behave in each workflow; scenarios specify it by example, and Scrut and a drawing check keep the examples true."
topics: [git, testing]
question: "Do you write down how your tool should behave before you build it?"
docs: ../git-splice/test/scenarios/README.md
---

git-splice is a tool, but the tool isn't what I care about. I care about the workflows: how should splicing behave when I work on a branch, when a pull request gets squash-merged, or when someone rewrites the other repository's history?

## Scenarios

For each of these situations, I write a scenario: a small example with a state before, a command, and the state after. That's specification by example: not "status shows how far the splice is ahead", but this command, in this situation, prints exactly this. Together, the scenarios are the specification:

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

## Examples that run

Each scenario is a Markdown file, and its examples run. I use Scrut for that, a tool from Meta. A code block marked `scrut` holds a command after the `$`, and below it the output I expect:

```console
$ git splice status
On branch main

  ahead 2, behind 3  lib
```

Scrut runs the command and compares. If git-splice prints anything else, the test fails.

## Drawings that are checked

The scenarios also draw the commit graphs. A drawing goes stale without anyone noticing, so a check reads it, looks up every commit and arrow in the real repositories, and names every difference:

```console
$ check_drawing <drawing>
!!   R points at d', the code says e'
!!   b' is solid, but no upstream branch has it: dash it
```

Text, output and drawings: together, they are the acceptance tests. Splicing works when they pass.

## Why build it, then?

The specification doesn't depend on Git. A tool for Sapling or Jujutsu that behaves as the scenarios say would splice just as well.

That I write the reference implementation at the same time shows that the specification can be built. And it keeps the specification honest: a scenario that no tool can fulfil shows up right away.
