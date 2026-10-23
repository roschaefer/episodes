---
slug: remotes-are-the-wrong-boundary
id: remote-boundary
title: "Git remotes are the wrong boundary for one directory"
description: "A remote always represents a repository. Naming one after a monorepo directory made a catastrophic push look ordinary—and revealed a flaw in git-subtrees' model."
series: splicing-concepts
seriesOrder: 7
topics: [git]
docs: ../git-splice/docs/design/accidental-monorepo-push.md
---

The original `git-subtrees` configuration had an appealing rule: the remote name was the directory path.

```text
vendor/parser  →  remote "vendor/parser"
libs/model     →  remote "libs/model"
```

There was no separate configuration file. Git already knew each URL, and remote-tracking refs already held the upstream branches. Unfortunately, the rule suggested something Git could not enforce: that a remote named `vendor/parser` represented only `vendor/parser/`.

It never did. A Git remote represents another **whole repository**.

## The dangerous command looks correct

The safe operation first extracts the directory and pushes the reconstructed commit:

```sh
git subtree push --prefix=vendor/parser vendor/parser main
```

But one omitted word changes its meaning completely:

```sh
git push vendor/parser main
```

Git now sends the monorepo's `main` branch—including every other directory and its history—to the parser repository. The remote name makes the command look scoped. Git sees no scope at all.

[Issue #50](https://github.com/roschaefer/git-subtrees/issues/50) documents less obvious routes to the same outcome. `push.autoSetupRemote` may choose the only configured remote. An IDE's Sync button follows a branch's accidentally configured upstream. LazyGit may suggest the first remote when there is no `origin`. `git push --all`, `--mirror`, shell history and force pushes create still more paths.

Deleting the branch afterward does not make the data private again. Anyone who fetched or forked it has a copy, and hosting providers may retain objects that remain addressable by SHA.

## My first response treated it as user error

The immediate fix was a `pre-push` hook. It inspected outgoing commits and rejected a monorepo-shaped tree when the target was a subtree remote.

That guardrail helped, but its limitations told me something:

- hooks are not cloned;
- `--no-verify` bypasses them;
- hook managers compete for the same entry point;
- every clone must install the protection correctly;
- every new way of pushing needs to remain covered.

I also explored disabling the push URL and implementing a custom remote protocol. Each option added machinery around a capability the tool did not need users to have.

## Remove the capability

Fetching does not require a configured remote. Git can fetch a URL directly into a private namespace:

```sh
git fetch <url> '+refs/heads/*:refs/splices/<path>/*'
```

Pushing does not require one either. Git Splice can rebuild the directory's commit and send that exact commit to an explicit URL and refspec.

The URL belongs in the directory's committed state file. Private refs retain the fetched branches for comparisons and merges. No named remote exists for an ordinary `git push` to target.

This removes more than one security risk. Remote names cannot collide. Moving a directory does not require renaming a remote. Completion menus stop suggesting upstream repositories as push targets. Fresh clones have the mapping immediately because it travels with the worktree.

The lesson was uncomfortable because remotes had made the first implementation pleasantly small. But a concise configuration is not necessarily a correct model. A directory-to-repository relationship needs a URL and refs; it does not need to pretend that the directory is itself a local repository.

The safest invalid operation is not one intercepted by a clever hook. It is one the design cannot express.
