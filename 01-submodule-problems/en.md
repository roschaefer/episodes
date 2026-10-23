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

Git has its own implementation of nested repositories, called `git submodule`. Unfortunately, submodules have a remarkably bad reputation. Let's have a look at why.

Let's build an example.

```console
# roschaefer.github.io/git-splice/docs/sandbox
git clone https://github.com/roschaefer/git-splice.git
cd git-splice
nix develop -c just sandbox comparisons/git-submodule
```

You can run the example yourself: these commands open a sandbox with the library and the monorepo, and every command there prints what you see here. The [git-splice documentation](https://roschaefer.github.io/git-splice/docs/sandbox/#any-page-in-a-sandbox) explains how.

The example builds a library with 30 commits and a monorepo with an app.

Then we add the library to the monorepo as a submodule. That one command, `git submodule add`, writes to six places:

```console
git submodule add https://git.example.com/lib.git vendor/lib
```

Then we commit the submodule:

```console
git commit -m "add lib as a submodule"
```

## Where a submodule keeps its state

```text
monorepo/
├── .gitmodules      2  name, path and URL
├── app/
│   └── main.txt
└── vendor/
    └── lib          1  gitlink: 160000 commit bafd496
```

1. The gitlink. Where the library is, the monorepo's commit holds only the ID of the library's checked-out commit. The commit itself isn't stored in the monorepo.

2. `.gitmodules`, a file that is committed like any other. It gives the submodule a name and maps it to a path and an upstream URL.

There are also [four more places](https://roschaefer.github.io/git-splice/test/comparisons/git-submodule/#where-a-submodule-keeps-its-state) outside the commit where Git keeps a submodule.

## Mistake 1: what belongs together is stored apart

Because the monorepo stores only the ID, it doesn't see the library's files. So when I change a file in the library and a file in the app, `git status` doesn't even show me the library file. It only tells me that the pointer to the submodule changed:

```console
$ git status --short
 M app/main.txt
 m vendor/lib
```

For this one change I need two commits in two repositories, and the second one feels redundant. First the bugfix *f* in the library, then *b* in the monorepo, which records nothing but the new pointer to *f*:

![The monorepo's a and b in a line. Below it, the library's l and f, each under the monorepo commit that records it](../git-splice/test/comparisons/git-submodule-fix.drawio.svg)

That has consequences. For example, I can push the monorepo and forget the library commit that goes with it. Then my colleagues get an error when they clone:

```console
$ git clone --recurse-submodules ../origin.git ../colleague
fatal: remote error: upload-pack: not our ref a6152f5cee8b2bfd6b5dfc7bbb2bf5d8a7562325
```

Other commands like `git log` don't look past the submodule's border either, because the monorepo only knows the pointer. The history of a library file is empty in the monorepo:

```console
git log --oneline -- vendor/lib/src/parse.txt
```

And why is the submodule's path in `.gitmodules` again? The gitlink already sits at that path.

## Mistake 2: "Shared mutable state is the root of all evil"

That's an old piece of wisdom from programming, and submodules run right into it.

Submodules also keep state outside the worktree, for example in the monorepo's `.git/config`. All worktrees share that file. I often use several worktrees to work in parallel. If I change the configuration in one worktree, for example the upstream URL, I've changed it *in all worktrees*:

```console
$ git -C ../feature config submodule.vendor/lib.url https://git.example.com/lib-fork.git
$ git config submodule.vendor/lib.url
https://git.example.com/lib-fork.git
```

A classic case of shared mutable state. According to the Git documentation, the support for submodules in worktrees is incomplete. If you try anyway and want to remove a worktree with submodules again, you get a scary error:

```console
$ git worktree remove ../feature
fatal: working trees containing submodules cannot be moved or removed
```

## What I want instead

Shouldn't the monorepo carry everything it needs to live? Why is a submodule's state kept in so many different places? The library's files could be in the monorepo commit like any other files, and a single file in the library's folder would be enough to remember where it came from.

Then a single commit *c* changes the library and the app:

![The monorepo's s and c in a line. Below it, the library's l, with main at l](../git-splice/test/comparisons/git-submodule-splice-fix.drawio.svg)

The library has no new commit yet. Its `main` stays at *l* until I decide to send the bugfix there.
