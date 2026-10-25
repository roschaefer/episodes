---
slug: separate-histories-shared-files
title: "Separate histories, shared files"
description: "Copy the other repository's files into a folder, remember the last synced commit, and that commit is the base of a three-way merge."
series: why-splicing
seriesOrder: 4
topics: [git]
question: "What else would you need to keep two repositories in sync for good?"
docs: ../git-splice/test/concepts/splice-file/README.md
---

Neither Git submodules nor `git subtree` are a good way to keep two repositories in sync continuously.

To combine the best of both worlds, we need separate histories, as with submodules. At the same time, the monorepo should contain the sub-repository's files, as with `git subtree`. That way, the standard commands like `git status` and `git log` keep working the way you're used to.

## Just the files

That's simpler than it sounds. We copy the other repository's files into a folder of the monorepo, and that's it:

```text
monorepo/
├── app/
│   └── main.js
└── vendor/a/       the files of a.git
    └── src/
        └── parse.js
```

No commits are exchanged. The monorepo doesn't get the other repository's history, and the other repository doesn't get the monorepo's. A fix in `vendor/a/` and the code in `app/` that calls it are one ordinary commit.

## A sync point

We only remember one thing: which commit of the other repository we last copied. It's similar to a gitlink, but it doesn't promise to be the checked-out commit. It's enough for it to be the last *synced* commit. A small file in the folder keeps it, along with the URL we know from `.gitmodules`:

```text
[splice]
	commit = 3f1c…
[upstream "origin"]
	url = git@github.com:x/a.git
```

The file is committed, so it moves along with the folder, and rewriting commits can't lose it.

## A three-way merge

In the meantime, both sides move on. To bring them together, a plain three-way merge is enough:

```text
BASE     vendor/a/ as we last copied it, at 3f1c…
OURS     vendor/a/ in the monorepo, as it is now
THEIRS   a.git, as it is now
```

The sync point is the base. Git compares our files and theirs with it and takes the changes of both sides. We don't have to bring two histories into line as with `git subtree`; it's only about changes to files.

If different branches sync at different times, the sync point can conflict. But that's intended, and we resolve it the way we're used to in Git.
