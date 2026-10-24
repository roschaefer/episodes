---
slug: git-subtree
title: "Git Subtree"
description: "git subtree fügt überflüssige Merge-Commits in die Git-Historie ein. Eine lineare Historie bekommt man damit nicht."
series: why-splicing
seriesOrder: 3
topics: [git]
question: "Habt ihr schon mal Git-Subtrees benutzt, um ein anderes Repository zu vendoren?"
docs: ../git-splice/test/comparisons/git-subtree.md
---

Seit 2012 gibt es das Skript `git subtree`, das meist zusammen mit Git installiert wird. Damit importiert man die Commit-Historie eines anderen Repositorys in ein Monorepo.

Auch das ist ein vielversprechendes Konzept, denn dadurch leben alle Commits im selben Monorepo. Die Standardbefehle wie `git status` und `git log` funktionieren also so, wie man es gewohnt ist.

Wir schauen uns das an einem Beispiel an. Das Monorepo hat 40 Commits, das andere Repository 30:

```console
# roschaefer.github.io/git-splice/test/comparisons/git-subtree
git subtree add --prefix=vendor/lib https://git.example.com/lib.git main
```

Allerdings zieht `git subtree` dabei die gesamte Historie des anderen Repositorys mit ins Monorepo. Danach hat das Monorepo 71 Commits:

```console
$ git log --graph --format=%s -4
*   Add 'vendor/lib/' from commit 'bafd496b1f4512a95b69464604f3da428aa9e33b'
|\
| * lib commit 30
| * lib commit 29
| * lib commit 28
```

## `--squash`

`git subtree` bringt auch eine Option mit, die Historie des anderen Repositorys zu squashen:

```console
git subtree add --squash --prefix=vendor/lib https://git.example.com/lib.git main
```

Allerdings versteht `git subtree` unter `--squash` etwas Eigenartiges. Statt eines einzigen Commits squasht es nur das andere Repository zu einem Commit *q*, und ein Merge-Commit *s* des Monorepos joint ihn ein. Es entstehen also immer zwei Commits statt einem:

![Die Commits a und s des Monorepos in einer Reihe, und q, ein Commit ohne Eltern, als zweiter Elternteil von s](../git-splice/test/comparisons/git-subtree-squash-add.drawio.svg)

Weil dann die Historie fehlt, muss `git subtree` bei jedem Push neu berechnen, welche Commits das andere Repository noch nicht kennt. Sagen wir, *c* und *e* fixen das Sub-Repository, *b* und *d* ändern die App:

![Die Commits a, s, b, c, d und e des Monorepos in einer Reihe, und q als zweiter Elternteil von s](../git-splice/test/comparisons/git-subtree-squashed.drawio.svg)

Um *c* und *e* zu finden, durchsucht `git subtree split` auf einmal die gesamte Historie des Monorepos, hier 46 Commits, obwohl nur zwei davon zählen. Nur mit `--squash` skaliert das nicht.

## `--rejoin`

Dieses Problem soll ein weiteres Flag lösen, `--rejoin`. Damit legt `git subtree` bei jedem Push einen Sync-Punkt in der Historie ab, wieder einen gesquashten Commit und einen Merge. Ähnlich wie bei Submodulen entstehen also viele Commits, die sich völlig überflüssig anfühlen. Mit `--squash` entstehen zwei Commits beim Pullen, mit `--rejoin` zwei weitere bei jedem Push.

Die Historie sieht entsprechend durcheinander aus. Hier sind es drei Sub-Repositorys, zweimal in derselben Reihenfolge gepusht:

![Die Historie des Monorepos mit Merges für drei Sub-Repositorys x, y und z, zweimal in derselben Reihenfolge rejoined. Die gesquashten Commits jedes Sub-Repositorys bilden eine eigene Reihe, und die Pfeile von y und z zu ihren Merges kreuzen die Reihen darüber](../git-splice/test/comparisons/git-subtree-rejoin-three.drawio.svg)

Dieses Muster habe ich gesehen, als ich mein Tool zunächst auf `git subtree` aufgebaut hatte.

Die Sync-Punkte findet `git subtree` über Hinweise in den Commit-Nachrichten, Zeilen wie `git-subtree-split: <commit>`. Fasst ein Rewrite Commits zusammen und gehen dabei die ursprünglichen Nachrichten verloren, etwa beim Squash-Merge eines Pull Requests, dann findet `git subtree` auch die Sync-Punkte nicht mehr.

All das zeigt: `git subtree` ist das falsche Werkzeug, wenn man zwei Repositorys mit unterschiedlichen Historien hin und her synchronisieren möchte. Gut geeignet ist es dagegen, wenn man aus zwei Repositorys eins machen möchte. Das ist in unserem Anwendungsfall aber nicht so.
