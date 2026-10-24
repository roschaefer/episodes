---
slug: git-submodules
title: "Git Submodules"
description: "One git submodule add writes to six places. The commit records a pointer, not the change, and the rest is state that clones and worktrees share in different ways."
series: why-splicing
seriesOrder: 2
topics: [git]
question: "Have you ever used Git submodules, and what was your developer experience?"
docs: ../git-splice/test/comparisons/git-submodule.md
---

Git has its own implementation of nested repositories: submodules.

"Submodule" – that sounds like the right concept. But unfortunately, using them is quite error-prone. Let's have a look at why. So let's build an example:

```console
# roschaefer.github.io/git-splice/docs/sandbox
git clone https://github.com/roschaefer/git-splice.git
cd git-splice
nix develop -c just sandbox comparisons/git-submodule
```

By the way: you can run the example yourself. These commands open a sandbox with the submodule and the monorepo, and every command prints what you see here. The [git-splice documentation](https://roschaefer.github.io/git-splice/docs/sandbox/#any-page-in-a-sandbox) explains how.

The example builds a monorepo and another repository with 30 commits.

Then we add the other repository to the monorepo as a submodule. That one command, `git submodule add`, writes to six places in total:

```console
git submodule add https://git.example.com/lib.git vendor/lib
```

Now we commit the submodule in the monorepo:

```console
git commit -m "add lib as a submodule"
```

## Where a submodule keeps its state

```text
monorepo/
├── .gitmodules      name, path and URL
├── app/
│   └── main.txt
└── vendor/
    └── lib          gitlink: 160000 commit bafd496
```

- At the submodule's folder path, the monorepo's commit holds only a so-called gitlink, with the ID of the submodule's checked-out commit. The commit itself isn't stored in the monorepo.

- The root folder has one more file, `.gitmodules`. It gives the submodule a name and stores the folder path to the submodule and its upstream URL, much like a `git remote`.

There are also [four more places](https://roschaefer.github.io/git-splice/test/comparisons/git-submodule/#where-a-submodule-keeps-its-state) where Git keeps a submodule. But only the two above end up in the commit.

## Mistake 1: what belongs together is stored apart

Because the monorepo stores only the submodule's commit ID, it doesn't see the submodule's files. Say I change one file inside the submodule and one outside it:

```console
echo "fix" >>vendor/lib/src/parse.txt
echo "call parse()" >>app/main.txt
```

Then `git status` doesn't even show me the changes inside the submodule. It only tells me that the pointer to the submodule changed:

```console
$ git status --short
 M app/main.txt
 m vendor/lib
```

For this one change I need two commits in two repositories. First the bugfix *f* in the submodule, then *b* in the monorepo, which records nothing but the new pointer to *f*:

![The monorepo's a and b in a line. Below it, the submodule's l and f, each under the monorepo commit that records it](../git-splice/test/comparisons/git-submodule-fix.drawio.svg)

That has consequences. For example, I can push the monorepo and forget the submodule's commit that goes with it. Then my colleagues get an error when they clone:

```console
$ git clone --recurse-submodules ../origin.git ../colleague
fatal: remote error: upload-pack: not our ref a6152f5cee8b2bfd6b5dfc7bbb2bf5d8a7562325
```

Other commands like `git log` don't look past the submodule's border either, because the monorepo only knows the pointer. The history of a file in the submodule is empty in the monorepo:

```console
git log --oneline -- vendor/lib/src/parse.txt
```

And why is the submodule's path in `.gitmodules` again? The gitlink already sits at that path:

```text
monorepo/
├── .gitmodules      path: vendor/lib
├── app/
│   └── main.txt
└── vendor/
    └── lib          here the path is implicit
```

## Mistake 2: "Shared mutable state is the root of all evil"

"Shared mutable state is the root of all evil" – that's a well-known trap in programming, and submodules run right into it.

Submodules also keep global state outside the worktree, for example in the monorepo's `.git/config`. All worktrees share that file. I often use several worktrees to work in parallel. If I change the configuration in one worktree, for example the upstream URL, I've changed it *in all worktrees*:

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

Shouldn't the monorepo carry everything it needs to live? Why is a submodule's state scattered across so many different places? The submodule's files could just be in the monorepo commit, like all other files.

From within the monorepo, a single commit *c* could change the submodule's files and the monorepo's at the same time:

![The monorepo's s and c in a line. Below it, the library's l, with main at l](../git-splice/test/comparisons/git-submodule-splice-fix.drawio.svg)

Only when I decide to bring the bugfix to the submodule's repository would I send a commit there.
