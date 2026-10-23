---
slug: what-goes-wrong-with-git-submodules
id: submodule-problems
title: "What goes wrong with Git submodules"
description: "One git submodule add writes to six places. The commit records a pointer, not the change, and the rest is state that clones and worktrees share in different ways."
series: why-splicing
seriesOrder: 2
topics: [git]
question: "Have you ever used Git submodules, and what was your developer experience?"
docs: ../git-splice/test/comparisons/git-submodule.md
---

I work on an app that uses a library from another repository. While working on the app I find a bug in the library. The bugfix and the code that calls it belong together, so I want to make them in one go, test them together and commit them together.

With the library as a submodule, that's where it starts to go wrong. To see why, I first show how a submodule works. I add the library to my monorepo with one command, `git submodule add`. That one command writes to six places.

## Where a submodule keeps its state

```console
$ git ls-tree HEAD vendor/lib
160000 commit bafd496b1f4512a95b69464604f3da428aa9e33b	vendor/lib
```

First, the commit. The monorepo's tree has an entry with the mode 160000, a so-called gitlink. It holds the ID of one library commit. Only the ID: the library's commit itself isn't in the monorepo.

```console
$ git ls-files --stage vendor/lib
160000 bafd496b1f4512a95b69464604f3da428aa9e33b 0	vendor/lib
```

Second, the index, the file in `.git` where Git prepares the next commit. It has the same entry. To see whether the submodule changed, Git doesn't look at the library's files. It compares the library's `HEAD` with this ID.

```console
$ cat .gitmodules
[submodule "vendor/lib"]
	path = vendor/lib
	url = https://git.example.com/lib.git
```

Third, `.gitmodules`, a file that is committed like any other. It gives the submodule a name and maps the name to a path and a URL.

```console
$ git config --get-regexp '^submodule\.'
submodule.vendor/lib.url https://git.example.com/lib.git
submodule.vendor/lib.active true
```

Fourth, the monorepo's `.git/config`. Git copied the URL here. In a fresh clone, `git submodule init` makes that copy. And to clone the library, Git uses this copy, not `.gitmodules`.

```console
$ cat vendor/lib/.git
gitdir: ../../.git/modules/vendor/lib
```

Fifth, the library's folder. Its `.git` isn't a repository, only a file that points to one.

```console
$ git -C vendor/lib config --get-regexp 'core.worktree|remote.origin.url'
core.worktree ../../../../vendor/lib
remote.origin.url https://git.example.com/lib.git
```

Sixth, the library's own repository, hidden in `.git/modules`. Its config points back at the folder. And it has the URL a third time, the one its fetches use.

I think this design makes two mistakes, and everything else follows from them.

## Mistake 1: what belongs together is stored apart

The monorepo stores a URL and one library commit, but never the library's files. So when I change a file in the library and a file in the app, `git status` doesn't even show me the library file. It only tells me that the submodule changed:

```console
$ git status --short
 M app/main.txt
 m vendor/lib
```

To commit, I need two commits in two repositories. First the bugfix *f* in the library, then *b* in the monorepo, which records nothing but the new pointer to *f*:

![The monorepo's a and b in a line. Below it, the library's l and f, each under the monorepo commit that records it](../git-splice/test/comparisons/git-submodule-fix.drawio.svg)

The monorepo commit *b* doesn't carry the change. It carries a reference to a commit that, at this point, exists only on my machine. That has consequences:

- `git log -- vendor/lib/src/parse.txt` in the monorepo is empty. The monorepo has no history of the library's files.
- I have to push in the right order. If I push the monorepo first, my colleagues get a commit they can't check out: `fatal: remote error: upload-pack: not our ref`.
- My colleagues end up in the library on a detached `HEAD`. If they want to fix something there, they need to create a branch first.

A commit is supposed to be a snapshot of what I changed. With a submodule, half of my change is somewhere else.

## Mistake 2: shared mutable state

"Shared mutable state is the root of all evil" is an old rule from programming, and submodules run right into it.

The six places don't even live equally long. The gitlink and `.gitmodules` are committed, so everyone gets them. The index, the pointer file and the library's repository belong to one worktree. I use `git worktree` a lot, to have a second branch checked out next to the first one. In a new worktree, the submodule is empty, and it gets its own clone of the library under `.git/worktrees/<name>/modules/`.

But the config belongs to the clone, and all of its worktrees share it. If I point the submodule at my fork in one worktree, I've changed it in all of them:

```console
$ git -C ../feature config submodule.vendor/lib.url https://git.example.com/lib-fork.git
$ git config submodule.vendor/lib.url
https://git.example.com/lib-fork.git
```

And the copies drift apart. If a colleague changes the URL in `.gitmodules`, my clone keeps fetching from the old one, until I run `git submodule sync`. Nothing tells me which of the places is right. Git also refuses to move or remove a worktree that contains submodules, unless I use `--force`. The Git documentation is honest about it: "the support for submodules is incomplete. It is NOT recommended to make multiple checkouts of a superproject."

## What I want instead

The library's files should be in the monorepo commit, like any other files. Then the bugfix and the code that calls it are one commit, `status` and `log` see every file, and every worktree has the library without any setup:

![The monorepo's s and c in a line. Below it, the library's l, with main at l](../git-splice/test/comparisons/git-submodule-splice-fix.drawio.svg)

Here *c* changes the library and the app in one commit. The library has no new commit yet. Its `main` stays at *l* until I decide to send the bugfix there. How that works is what this series is about.

## Where submodules are still better

Submodules have real strengths. A clone without `--recurse-submodules` doesn't download the library at all. The monorepo commit pins an exact library commit. And the library can stay private while the monorepo is public, or the other way round. If those things matter most to you, submodules are a reasonable choice.
