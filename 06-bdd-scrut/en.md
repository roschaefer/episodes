---
slug: specification-by-example-with-scrut
title: "Specification by example with Scrut"
description: "git-splice's documentation is its test suite: Scrut runs the commands in the Markdown and compares their output."
series: building-git-splice
seriesOrder: 1
topics: [git, testing]
question: "Who writes and who checks the acceptance tests in your team?"
docs: ../git-splice/README.md
---

The documentation of git-splice is also its test suite. I use Scrut for that, a tool from Meta. In a Markdown file, a code block marked `scrut` holds a command after the `$`, and below it the output I expect:

```console
$ git splice status
On branch main

  ahead 2, behind 3  lib
```

Scrut runs the command and compares. If git-splice prints anything else, the test fails. So the README you read is the same file the CI runs, and it can't fall behind the tool.

## Three terms

A **test** checks that code does what it should. Usually it's written in code, for developers.

**Specification by example** goes a step further: the requirement itself is written as concrete examples. Not "status shows how far the splice is ahead", but this command, in this situation, prints exactly this.

**Acceptance test-driven development** writes these examples before the code. They are the acceptance tests: the feature is done when they pass.

## The roles swap

In classic ATDD, the product owner checked the acceptance tests, and the developer implemented them.

With AI agents, the roles swap. I check the acceptance tests, and the agent implements them.

For me, that's a good way to work with AI.
