---
slug: git-subtree
title: "Git Subtree"
description: "git subtree adds needless merge commits to the Git history. It doesn't give you a linear history."
series: why-splicing
seriesOrder: 3
topics: [git]
question: "Have you ever used Git subtrees in order to vendor another repository?"
docs: ../git-splice/test/comparisons/git-subtree.md
---

Since 2012, there has been a script called `git subtree`, which is usually installed along with Git. It imports the commit history of another repository into a monorepo.

```console
$ man git-subtree
NAME
     git-subtree - Merge subtrees together and split repository
     into subtrees

DESCRIPTION
     Subtrees allow subprojects to be included within a
     subdirectory of the main project, optionally including the
     subproject’s entire history.
```

That's a promising concept too, because all commits then live in the same monorepo. So the standard commands like `git status` and `git log` work just the way you're used to.

Let's look at an example. The monorepo has 40 commits, the other repository 30:

```console
# roschaefer.github.io/git-splice/test/comparisons/git-subtree
git subtree add --prefix=vendor/lib \
  https://git.example.com/lib.git main
```

However, `git subtree` pulls the other repository's whole history into the monorepo. Afterwards, the monorepo has 71 commits:

```console
$ git log --graph --format=%s -4
*   Add 'vendor/lib/' from commit 'bafd496b1f4512a95b69464604f3da428aa9e33b'
|\
| * lib commit 30
| * lib commit 29
| * lib commit 28
```

But do I even want that? In a monorepo that I vendor another repository into, I don't need its commits at all. I just want to copy the repository in. Maybe I then add some code that wires it into my app. That part belongs in the monorepo's history, because it's the integration.

## `--squash`

`git subtree` also comes with an option to squash the other repository's history:

```console
git subtree add --squash --prefix=vendor/lib \
  https://git.example.com/lib.git main
```

However, `git subtree` has a peculiar idea of what `--squash` means. Instead of a single commit, it squashes only the other repository into a commit *q*, and a merge commit *s* of the monorepo joins it in. So you always get two commits instead of one:

![The monorepo's commits a and s in a line, and q, a commit without parents, as the second parent of s](../git-splice/test/comparisons/git-subtree-squash-add.drawio.svg)

Because the history is missing then, `git subtree` has to work out again on every push which commits the other repository doesn't know yet. `git subtree split` reads where it can start from the commit messages. `add`, `pull` and `split --rejoin` write lines like `git-subtree-split: <commit>` into them. Only a `git-subtree-mainline:` line tells `split` up to which commit it already knows the monorepo's history. Without `--squash`, `add`'s merge has that line; *q* doesn't:

```console
$ git log -1 --format=%B HEAD~4^2 | grep '^git-subtree-'
git-subtree-dir: vendor/lib
git-subtree-split: bafd496b1f4512a95b69464604f3da428aa9e33b
```

Say *c* and *e* fix the sub-repository, and *b* and *d* change the app. To find *c* and *e*, outlined in orange, `git subtree split` suddenly searches the monorepo's whole history, filled in grey. That's 46 commits here, since *a* stands for 40 app commits, and only two of them matter:

![The monorepo's commits a, s, b, c, d and e in a line, and q as the second parent of s. All of them are grey, as split walks them, and c and e are outlined orange, as it finds them](../git-splice/test/comparisons/git-subtree-split-walks.drawio.svg)

With only `--squash`, that doesn't scale.

## `--rejoin`

Another flag is meant to solve this problem: `--rejoin`. With it, `git subtree` leaves a sync point in the history on every push, again a squashed commit *r* and a merge *j*. *j*'s message has what *q*'s lacks, the `git-subtree-mainline:` line:

```console
$ git log -1 --format=%B | grep '^git-subtree-'
git-subtree-dir: vendor/lib
git-subtree-mainline: 9d3cc6061455cb38432ce9846218e1227e4771be
git-subtree-split: 48108daa0f798109c3e672ed47a7de6204cf4e02
```

After that, `split` only walks the commits from the sync point on. After two more commits *g* and *h*, that's five:

![The monorepo's commits a, s, b, c, d, e, j, g and h in a line. Below it, q as the second parent of s, and r, on top of q, as the second parent of j. e, r, j, g and h are grey, as split walks them, and h is outlined orange, as it finds it](../git-splice/test/comparisons/git-subtree-rejoin-walks.drawio.svg)

The price for it: much like with submodules, you get lots of commits that feel completely unnecessary. With `--squash`, pulling makes two commits, and with `--rejoin`, every push makes two more.

The history looks just as messy. Here with three sub-repositories, pushed twice in the same order:

![The monorepo's history with merges for three sub-repositories x, y and z, rejoined twice in the same order. Each sub-repository's squashed commits form their own line, and the arrows from y and z to their merges cross the rows above them](../git-splice/test/comparisons/git-subtree-rejoin-three.drawio.svg)

I saw this pattern when I first built my tool on top of `git subtree`.

Because the sync points live only in the commit messages, they get lost as soon as a rewrite combines commits, for example when a pull request is squash-merged. Then `split` searches the whole history again.

All of this shows: `git subtree` is the wrong tool if you want to synchronize two repositories with different histories back and forth. It's a good fit, though, if you want to turn two repositories into one. But that's not our use case.
