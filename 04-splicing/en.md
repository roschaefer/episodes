---
title: "Splicing"
description: "The concept gets a name: a splice is a folder together with its connection to another repository, and git-splice is its reference implementation."
topics: [git]
question: "Can you think of a better name? Ideally an everyday word that no version control system uses yet."
docs: ../git-splice/docs/design/name.md
---

In the last episode, we put three things together: we copy the other repository's files into a folder, remember the last synced commit, and bring both sides together with a three-way merge. That concept needs a name. I call it splicing.

A splice joins two things into one: two ropes, two pieces of film, two cables. In a long splice, the strands of two ropes are woven into each other. Unlike a knot, it leaves no lump, and the rope still runs through a pulley:

![Rope splices from the Nordisk familjebok, a long splice on the left](../git-splice/docs/images/rope-splices-nordisk-familjebok.png)

That's what we do with another repository. Its files are woven into the monorepo as an ordinary folder, with no gitlink and nothing extra to check out. The only trace of the joint is one small file in that folder.

## Noun and verb

The word works as a noun and as a verb:

```text
a splice     the folder, with its connection
             to the other repository
splice in    bring the other repository's
             changes into the folder
splice out   send the folder's changes back
             to the other repository
```

## A name for a concept

Splicing is a concept, not a tool. git-splice is its reference implementation, for Git. Other version control systems could splice too.

So the name must not collide with the words of the version control system it's built into. Words like `pull`, `upstream` or `rebase` keep the meaning they have there. A new word like "splice" has to be coined: hardly anyone knows yet what a splice is in version control. Everyday words would be easier, but most of them are taken.
