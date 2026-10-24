---
slug: what-goes-wrong-with-git-subtree
title: "What goes wrong with git subtree"
description: "git subtree either imports the library's whole history or walks the monorepo's whole history on every push. And a remote per library is one typo away from publishing the monorepo."
series: why-splicing
seriesOrder: 3
topics: [git]
question: "Have you ever used Git subtrees in order to vendor a library?"
docs: ../git-splice/test/comparisons/git-subtree.md
---

`git subtree` gets the first part right. It puts the library's files into a folder of the monorepo, so a fix in the library and the code that calls it can be one commit. `git subtree split` and `git subtree push` turn the monorepo commits that touched the folder back into library commits.

git-splice started as a wrapper around `git subtree`. I dropped it for three reasons.

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

## Reason 3: a remote per library is one typo away from publishing the monorepo

`git subtree push` needs a remote, or a URL every time. My wrapper added one Git remote per library and named it like the folder. That looks tidy, until you type `git push vendor/lib main` instead of `git subtree push --prefix=vendor/lib vendor/lib main`. Then the whole monorepo lands in the library's repository, including folders that were never meant to leave it.

It doesn't take a typo. A plain `git push` with `push.autoSetupRemote`, an IDE's sync button, or a search in the shell history can do the same. Deleting the branch afterwards doesn't unpublish anything. I'll come back to this in its own episode.

## Where `git subtree` is the right tool

If you move a repository into a monorepo for good and retire its old home, `git subtree add` without `--squash` is exactly right. The history comes along, and `git blame` keeps working.

## What I took away

I wanted the library's files in the monorepo, without the library's history, without merges that only exist to make pushing fast, with a push that only looks at what changed since the last sync, and without a Git remote for each library. The next episodes show how that fits together.
