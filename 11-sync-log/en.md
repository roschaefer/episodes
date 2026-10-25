---
title: "Once the sync state exists, the log becomes trivial"
description: "A committed boundary turns 'what will push?' and 'what will pull?' from bespoke subtree analysis into ordinary Git set operations."
topics: [git]
---

[Issue #51](https://github.com/roschaefer/git-subtrees/issues/51) began as a modest usability request: before pushing a directory, show the commits that will be published.

`git subtrees diff` could show file changes, but a push publishes commits. Commit messages may have been written for a private monorepo audience. Author and committer identities become public. Creating a new upstream branch may publish far more commits than expected. Seeing only the final diff hides all of that.

In the old design, answering the question meant first running the expensive operation from issue #30: `git subtree split` the directory, then compare the resulting commit with remote-tracking branches. The feature looked small, but depended on the slowest and most complicated part of the system.

The `.splice` state changed that.

## Two histories with a known joint

Let `U` be the upstream commit recorded in `.splice`. From the corresponding local boundary, Git Splice deterministically rebuilds the later directory commits. Call the rebuilt tip `R`.

After fetching the target branch into a private ref, the two sides are ordinary Git histories:

```text
rebuilt local history:  U -- L1 -- L2   (R)
                                  \
fetched upstream:        U -- X1 -- X2  (remote)
```

There is no subtree-specific log algorithm left to invent. Git already knows how to subtract and compare commit sets.

## Outgoing and incoming

What a push would publish is everything reachable from `R` but not from the fetched branch:

```sh
git log R --not refs/splices/<path>/<branch>
```

What a pull would bring is the reverse:

```sh
git log refs/splices/<path>/<branch> --not R
```

To show both directions together:

```sh
git log --left-right --cherry-mark --oneline \
  R...refs/splices/<path>/<branch>
```

`<` and `>` identify the side. `=` marks equivalent patches, which matters when one side cherry-picked or rebased a change and therefore gave it a different commit ID.

If the upstream branch does not exist yet, the question becomes “which rebuilt commits are absent from every fetched branch?”:

```sh
git log R --not --glob='refs/splices/<path>/*'
```

Adding `--stat` displays the paths exactly as the upstream repository will see them, because the rebuilt commits already have the directory at their root. A custom format can expose author and committer identities before publication.

## The command became a consequence

The interesting part is not that these commands are short. It is that the user-facing feature no longer requires special reasoning.

In `git-subtrees`, `status`, `diff`, `pull`, `push` and the proposed `log` each had to recover part of the relationship from configured remotes and synthetic merge history. With committed upstream state and a deterministic local projection, they all operate on the same two tips.

This is the kind of simplification I look for in a redesign. A good primitive does not merely make one function easier. It makes several functions fall out of the model.

The final `log` interface can still make opinionated choices: default to all splices, group output by directory, show direction labels and accept familiar `git log` formatting options. But underneath, it is just Git comparing two histories whose joint is no longer hidden.
