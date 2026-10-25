---
title: "Vendoring does not require importing history"
description: "git subtree's squash mode hides upstream commits but still adds a side history and merge. A vendored tree needs a reference to upstream—not upstream ancestry."
topics: [git]
---

Christophe Porteneuve's [guide to Git subtrees](https://medium.com/@porteneuve/mastering-git-subtrees-943d29a798ec) demonstrates a surprise in `--squash`: it reduces the imported commits, but still maintains a subtree-specific pseudo-branch and merges it on every pull. Porteneuve argues that this clutters the graph indefinitely.

The name suggests a linear result: take many upstream commits, squash them into one monorepo commit. That is not what `git subtree pull --squash` produces.

## Squashed content, non-linear graph

Git's own [subtree documentation](https://github.com/git/git/blob/master/contrib/subtree/git-subtree.adoc) describes `--squash` as producing one commit containing the imported differences. The implementation then merges that synthetic commit with `--no-ff`.

One pull therefore adds two commits:

```text
*   M  Merge commit S as 'vendor/parser'
|\
| * S  Squashed 'vendor/parser/' changes from U1..U2
|/
*   A  Previous monorepo commit
```

`S` belongs to a synthetic side history. `M` connects it to the monorepo. The individual upstream commits are absent, but the monorepo is still non-linear.

That shape is not accidental bookkeeping. Later `git subtree` operations use it to find the old upstream point. Remove the side parent during a rebase or squash merge and the files may remain while the relationship disappears.

That complaint resonated with me: `git subtree` asks developers to accept surprising history in exchange for treating the vendored code as normal files. I had automated the commands, but automation did not remove the underlying coupling.

## Which history needs to explain which repository?

The turning point was to separate two questions.

The monorepo history should explain:

- when its copy of `vendor/parser` changed;
- which other monorepo changes shipped with it;
- which upstream revision that copy corresponds to.

The parser repository history should explain:

- how the parser evolved as an independent project;
- which monorepo changes were published back;
- their authorship and ordering in parser paths.

Neither repository needs the other's commits as ancestors.

For vendoring, a normal monorepo commit plus a checked-in upstream commit ID is enough:

```text
* P  splice: pull vendor/parser to 206f2a2
* A  Previous monorepo commit
```

`P` changes the directory and its `.splice` file together. The state file says which upstream tree was integrated. Fetched upstream commits can remain under private refs for merging and inspection without becoming ancestors of the monorepo branch.

## Pushing can rebuild the other view

Local monorepo commits still need to become meaningful upstream commits. That does not require storing the rebuilt history in the monorepo graph.

Git Splice walks commits since the recorded boundary that touched the directory. For each one it writes the directory as a root tree, removes `.splice`, maps parents and preserves the original author, committer, dates and message. The result is a deterministic upstream-shaped history which can be pushed directly.

These commits are a projection of monorepo history, not ancestors the monorepo must retain. They can live in private refs and be recreated when needed.

This clarified the design more than any optimization did: synchronization needs a verifiable correspondence between two histories, not one combined history. Once I stopped asking the commit graph to represent both repositories simultaneously, pulls became ordinary commits and vendoring stopped imposing merge topology on the monorepo.
