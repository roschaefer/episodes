---
slug: separate-histories-shared-files
title: "Separate histories, shared files"
description: "Separate histories as with submodules, the files in the monorepo as with git subtree, and between them a committed sync point."
series: why-splicing
seriesOrder: 4
topics: [git]
question: "What else would you need to keep two repositories in sync for good?"
docs: ../git-splice/test/concepts/splice-file/README.md
---

Neither Git submodules nor `git subtree` are a good way to keep two repositories in sync continuously.

To combine the best of both worlds, we need separate histories, as with submodules. At the same time, the monorepo should contain the sub-repository's files, as with `git subtree`. That way, the standard commands like `git status` and `git log` keep working the way you're used to.

## A sync point

For recomputing the commits to scale, we need a sync point. It's similar to a gitlink, but it doesn't promise to be the checked-out commit. It's enough for it to be the last *synced* commit.

The same file can also hold the configuration we know from `.gitmodules`, like the URL:

```text
[splice]
	commit = 3f1c…
[upstream "origin"]
	url = git@github.com:x/a.git
```

The file lives in the sub-repository's folder. So it always moves along with the folder, and because it's committed in the worktree, it works with several worktrees by design. Nor can rewriting the commits lose it, unlike `git subtree`'s sync points in the commit messages.

## A three-way merge

To reconcile the changed files, a plain three-way merge is enough. We don't have to bring two histories into line as with `git subtree`; it's only about changes to files.

If different branches sync at different times, this file can conflict. But that's intended, and we resolve it the way we're used to in Git.
