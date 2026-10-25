---
title: "Naming it git-splice"
description: "What a splice is, and the rule for git-splice's words: Git's words do what they do in Git, new words don't collide with them."
series: git-splice
seriesOrder: 1
topics: [git]
question: "Can you think of a better name? Ideally an everyday word that Git doesn't use yet."
docs: ../git-splice/docs/design/name.md
---

A splice joins two things into one: two ropes, two pieces of film, two cables. In a long splice, the strands of two ropes are woven into each other. Unlike a knot, it leaves no lump, and the rope still runs through a pulley.

git-splice does the same with another repository. Its files are woven into the monorepo as an ordinary folder, with no gitlink and nothing extra to check out. The only trace of the joint is one small file in that folder, `.splice`.

## A rule for names

When I name something in git-splice, I follow a rule in two parts:

1. Words from Git, like `status`, `pull`, `upstream` or `rebase`, do in git-splice what they do in Git.
2. New words must not collide with the ones Git already uses.

"Splice" is such a new word. Git doesn't use it, so it doesn't collide. But because it's new, I have to coin it: nobody knows yet what a splice is in Git.

So I'm still looking. "Splice" works so far, but I'd be happy with an everyday word that Git doesn't use yet.
