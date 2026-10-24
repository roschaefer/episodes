---
slug: git-subtree
title: "Git Subtree"
description: "git subtree adds needless merge commits to the Git history."
series: why-splicing
seriesOrder: 3
topics: [git]
question: "Have you ever used Git subtrees in order to vendor a library?"
docs: ../git-splice/test/comparisons/git-subtree.md
---

`git subtree` gets the first part right. It puts the library's files into a folder of the monorepo, so a fix in the library and the code that calls it can be one commit. `git subtree split` and `git subtree push` turn the monorepo commits that touched the folder back into library commits.

git-splice started as a wrapper around `git subtree`. I dropped it for two reasons.

## Reason 1: I don't want the library's history

Without `--squash`, `git subtree add` merges all of the library's commits into the monorepo. In my test setup, a monorepo with 40 commits has 71 after adding a library with 30 commits.

The monorepo uses the library. It doesn't develop the library's past. The changes the monorepo cares about, the ones that fit the library into the app, are monorepo commits anyway.

## Reason 2: with `--squash`, it doesn't scale

`--squash` keeps the library's history out. `add` creates a commit *q* with the library's files and no parents, and merges it as *s*:

![The monorepo's a and s in a line, and q, a commit without parents, as the second parent of s](../git-splice/test/comparisons/git-subtree-squash-add.drawio.svg)

Then I work. *c* and *e* fix the library, *b* and *d* change the app:

![The monorepo's a, s, b, c, d and e in a line, and q as the second parent of s](../git-splice/test/comparisons/git-subtree-squashed.drawio.svg)

To push the two fixes, `split` has to find out which commits touched the library. With `--squash`, the monorepo contains no library commit it could start from. So `split` walks the whole monorepo history, on every push. In my setup that's 46 commits, although only two of them matter. In a monorepo with years of history, that gets slow.

`split --rejoin` helps by merging the result back as a new starting point. That's one more merge *j* for every push, with another squashed commit *r* on top of *q*:

![The monorepo's a, s, b, c, d, e and j in a line. Below it, q as the second parent of s, and r, on top of q, as the second parent of j](../git-splice/test/comparisons/git-subtree-rejoin.drawio.svg)

And it breaks as soon as pull requests are squash-merged, which is common. The squash merge keeps the fixes but drops *j* and *r*, so the next `split` walks everything again:

![The monorepo's a, s and p in a line, and q as the second parent of s](../git-splice/test/comparisons/git-subtree-squash-merged.drawio.svg)

With one library, the graph is still readable. With three, every library adds its own squashed commits and its own merges, and their arrows cross:

![The monorepo's history with merges for three libraries. Each library's squashed commits form their own line, and the arrows from libraries B and C to their merges cross the lines of the other libraries](git-subtree-rejoin-three-libraries.drawio.svg)

None of these merges says anything about the app. They're there to make `split` fast.

## Where `git subtree` is the right tool

If you move a repository into a monorepo for good and retire its old home, `git subtree add` without `--squash` is exactly right. The history comes along, and `git blame` keeps working.

## What I took away

I wanted the library's files in the monorepo, without the library's history, without merges that only exist to make pushing fast, and with a push that only looks at what changed since the last sync. The next episodes show how that fits together.
