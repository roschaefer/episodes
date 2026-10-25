---
title: "Synchronization state belongs in the worktree"
description: "History can record a synchronization point, but ordinary history rewriting can erase it. A small committed state file survives and makes incremental work possible."
series: splicing-concepts
seriesOrder: 2
topics: [git]
---

To synchronize a directory, a tool needs to know where the previous synchronization ended. My first design delegated that question to `git subtree`.

A squashed pull writes identifying trailers such as `git-subtree-dir` and `git-subtree-split` into commits. Later operations search history for those markers. This avoids an extra file, but it turns a particular graph shape into a database.

That database is not stable in my workflow.

## Squash-merging erased the answer

I reproduced a routine sequence:

1. pull an upstream change on a feature branch;
2. make a local change in the same directory;
3. squash-merge the pull request into `main`;
4. ask `git-subtrees` for the directory's state.

The squash merge preserved the files but not the synchronization commit. `git-subtrees` classified the directory as diverged even though it contained only the upstream version plus a local change. A recovery pull could then cause the upstream commit to be exported twice.

The files survived. The meaning attached to the discarded graph did not.

## Exact classification had an increasing cost

I had already avoided some fragile bookkeeping by making status exact: rebuild the directory's upstream-shaped history with `git subtree split`, then compare ancestry with the remote branch.

That exposed [issue #30](https://github.com/roschaefer/git-subtrees/issues/30). `git subtree split` walks every commit reachable from `HEAD`, including commits that never touched the directory. On a monorepo with 670 commits, two locally changed directories increased `status` from 0.15 seconds to 2.86 seconds. Synthetic tests reached 44 seconds at 5,500 commits.

The recurring cost grew with the age of the monorepo, not with the amount of work since the last synchronization.

`git subtree split --rejoin` can add a checkpoint, but that checkpoint is another merge in history—and rebases and squash merges can remove it again. A cache under `.git` would be faster, but would not travel with a clone or branch.

## Commit the state, not the graph shape

Git Splice puts a small `.splice` file inside each synchronized directory. It records only facts owned by the upstream side:

```ini
[splice]
url = git@github.com:example/parser.git
commit = 206f2a2...
default-branch = main
```

The `commit` is the upstream commit whose tree the directory last matched. The file intentionally stores no monorepo commit SHA.

The local boundary can be derived: it is the newest commit in current history that changed `.splice`. A rebase may give that commit a new ID. A squash merge may combine it with local edits. Either way, current history still contains the moment when the recorded upstream state entered the directory.

From that boundary, rebuilding a push processes only later commits that touched the directory. The cost now follows new work instead of total repository age.

## Why the file lives inside the directory

Keeping `.splice` beside the content has useful consequences:

- `git mv` moves content and configuration together;
- a fresh clone can discover splices with `git ls-files`;
- branches carry the state that belongs to their version of the directory;
- a pull updates content and state in the same commit.

When exporting the directory, Git Splice omits `.splice` from the rebuilt tree. It is monorepo coordination data, not part of the upstream project.

Committed state is not automatically durable. `git-subrepo` also commits state, but its `parent` field stores a monorepo SHA that rebases and squash merges can invalidate. The important choice is not merely “file or history.” It is to store only stable facts and derive identities that belong to rewriteable history.
