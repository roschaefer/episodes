---
slug: publishing-parts-of-a-monorepo-independently
title: "Publishing parts of a monorepo independently"
description: "A directory should be developed inside a monorepo while being published as a standalone repository. Git offers submodules and subtrees for this—with very different drawbacks."
series: why-splicing
seriesOrder: 4
topics: [git]
---

A monorepo is convenient as long as everything in it can be developed together. But that does not mean everything should be published together. It may contain several tools while only some of them are open source. The intuitive arrangement is to keep each public project in a subdirectory that also appears as a standalone repository on GitHub.

Exporting that directory once is not enough. Dependencies get updated in the public repository, other people contribute changes, and that work needs to return to the monorepo. Meanwhile, new features are still developed together with the rest of the system and need to be published from there. The directory needs bidirectional synchronization.

The same problem appears from the other direction when vendoring. An application needs a change to a library but cannot wait for its next release. The team vendors the source into its monorepo, develops and tests the patch together with the application, and then wants to contribute it upstream. Because the team does not own the original repository, the change first needs to reach a branch in its own fork of the library.

Git offers two natural recipes for this: submodules and subtrees.

<!-- Set up a monorepo plus local upstream and fork repositories for the executable examples. -->
<!--
```scrut {fail_fast: true, output_stream: combined}
$ source "$TESTDIR/../scrut-setup.sh"
```
-->

## Recipe 1: Use the library as a submodule

A submodule lets the library remain a repository of its own. The monorepo merely records which commit should be checked out at `vendor/library`:

```scrut
$ git -c protocol.file.allow=always submodule add -q "$LIBRARY_FORK" vendor/library && \
> git commit -qm "application: add library as a submodule"
```

The patch is developed inside that nested repository. It is committed there and pushed directly to the team's fork:

```scrut
$ git -C vendor/library switch -qc feature/custom-patch && \
> printf '%s\n' "export const answer = 43;" >vendor/library/index.js && \
> git -C vendor/library add index.js && \
> git -C vendor/library commit -qm "library: support the application" && \
> git -C vendor/library push -qu origin feature/custom-patch && \
> git ls-remote --exit-code --heads "$LIBRARY_FORK" feature/custom-patch >/dev/null && \
> echo "patch is ready for a pull request"
patch is ready for a pull request
```

Finally, the monorepo has to record the new submodule commit too:

```scrut
$ git add vendor/library && \
> git commit -qm "application: use patched library"
```

Technically, this is a clean separation: the pull-request branch contains only library code and retains the library's original history. During everyday work, however, the team constantly deals with two repository states:

- A clone needs `--recurse-submodules` or a subsequent `git submodule update --init --recursive`.
- The submodule often starts on a detached `HEAD`; a branch must be checked out deliberately before committing.
- An application branch consists of commits in two repositories. They must be pushed in the right order so the recorded pointer remains reachable.
- Branch switches, rebases, and merge conflicts can involve both the monorepo and submodule working trees.
- IDEs, hooks, and CI need to know that `vendor/library` is not an ordinary directory.

Submodules model the repository boundary precisely. That is also why the boundary remains visible during almost every operation.

## Recipe 2: Use the library as a subtree

A subtree makes the opposite trade-off. The library's files are ordinary monorepo files. `git subtree` imports them below a prefix; `--squash` condenses their prior history:

```scrut
$ cd "$EXAMPLE_ROOT/subtree-monorepo" && \
> git remote add library "$LIBRARY_FORK" && \
> git subtree add --prefix=vendor/library --squash library main >/dev/null 2>&1 && \
> test -f vendor/library/index.js && echo "library is part of the working tree"
library is part of the working tree
```

The patch is now an ordinary monorepo commit. `git subtree push` reconstructs a branch rooted at `vendor/library` and pushes it to the fork:

```scrut
$ printf '%s\n' "export const answer = 43;" >vendor/library/index.js && \
> git add vendor/library/index.js && \
> git commit -qm "library: support the application" && \
> git subtree push --prefix=vendor/library library feature/custom-patch >/dev/null 2>&1 && \
> git ls-remote --exit-code --heads "$LIBRARY_FORK" feature/custom-patch >/dev/null && \
> echo "patch is ready for a pull request"
patch is ready for a pull request
```

The working-tree experience is much simpler: clones, branch switches, and application tests need no submodule commands. The repository pays elsewhere instead.

Even with `--squash`, the history does not stay linear. `git subtree add` creates a commit containing the condensed library history and merges it into the monorepo:

```scrut
$ git rev-list --min-parents=2 --count HEAD
1
```

Every later `git subtree pull --squash` extends that side history and creates another merge. Christophe Porteneuve demonstrates this surprising graph in detail in [Mastering Git subtrees](https://medium.com/@porteneuve/mastering-git-subtrees-943d29a798ec).

Writing changes back is not free either. `git subtree split` has to inspect the monorepo history and rebuild a history from the commits that touched the directory. This becomes noticeably slow in large, long-lived repositories; repeated pushes pay that cost again.

## Two valid models with different costs

Both recipes put the patch into a team-owned fork from which a pull request can be opened against the library:

- Submodules preserve the library's repository and history but move complexity into every checkout and many everyday Git commands.
- Subtrees give the team an ordinary monorepo working tree but move complexity into the commit graph and history reconstruction.

That is the underlying trade-off: a repository boundary needs to survive publication without constantly dictating work inside the monorepo. Git provides both building blocks, but neither approach makes that boundary invisible, linear, and cheap at the same time.
