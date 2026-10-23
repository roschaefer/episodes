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

The oldest way to have one repository inside another is called `git submodule`. Unfortunately, submodules have a remarkably bad reputation. Let's have a look at why.

Let's build an example.

```console
# roschaefer.github.io/git-splice/docs/sandbox
git clone https://github.com/roschaefer/git-splice.git
cd git-splice
nix develop -c just sandbox comparisons/git-submodule
```

You can run the example yourself: these commands open a sandbox with the library and the monorepo, and every command there prints what you see here. The [git-splice documentation](https://roschaefer.github.io/git-splice/docs/sandbox/#any-page-in-a-sandbox) explains how.

The example builds a library with 30 commits and a monorepo with an app. Then it adds the library to the monorepo as a submodule:

```console
git submodule add https://git.example.com/lib.git vendor/lib
```

That one command, `git submodule add`, writes to six places.

```console
git commit -m "add lib as a submodule"
```

Then we commit the submodule.

## Where a submodule keeps its state

```text
monorepo/
├── .gitmodules      2  name, path and URL
├── app/
│   └── main.txt
└── vendor/
    └── lib          1  gitlink: 160000 commit bafd496
```

1. The commit. The monorepo's tree has an entry with the mode 160000, a so-called gitlink. It holds the ID of one library commit. Only the ID: the library's commit itself isn't in the monorepo.

2. `.gitmodules`, a file that is committed like any other. It gives the submodule a name and maps the name to a path and a URL.

There are also [four more places](https://roschaefer.github.io/git-splice/test/comparisons/git-submodule/#where-a-submodule-keeps-its-state), which we don't see, where Git stores a submodule.

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

These places don't even live equally long. The gitlink and `.gitmodules` are committed, so everyone gets them. Others belong to a single worktree. I use `git worktree` a lot, to have a second branch checked out next to the first one. In a new worktree, the submodule is empty, and it gets its own clone of the library under `.git/worktrees/<name>/modules/`.

But a copy of the URL is in the monorepo's `.git/config`, and all worktrees share that file. If I point the submodule at my fork in one worktree, I've changed it in all of them:

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
