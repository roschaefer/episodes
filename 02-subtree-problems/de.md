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

Seit 2012 gibt es das Skript `git subtree`, das meist zusammen mit Git installiert wird. Damit importiert man die Commit-Historie eines anderen Repos in ein Monorepo.

Auch das ist ein vielversprechendes Konzept, denn dadurch leben alle Commits im selben Monorepo. Die Standardbefehle wie `git status` und `git log` funktionieren also so, wie man es gewohnt ist.

Wir schauen uns das an einem Beispiel an. Das Monorepo hat 40 Commits, das andere Repository 30:

```console
# roschaefer.github.io/git-splice/test/comparisons/git-subtree
git subtree add --prefix=vendor/lib \
  https://git.example.com/lib.git main
```

Allerdings zieht `git subtree` dabei die gesamte Historie des anderen Repos mit ins Monorepo. Danach hat das Monorepo 71 Commits:

```console
$ git log --graph --format=%s -4
*   Add 'vendor/lib/' from commit 'bafd496b1f4512a95b69464604f3da428aa9e33b'
|\
| * lib commit 30
| * lib commit 29
| * lib commit 28
```

Aber will ich das überhaupt? In einem Monorepo, in das ich ein anderes Repository vendore, brauche ich dessen Commits gar nicht. Ich will das Repository einfach nur hineinkopieren. Eventuell schreibe ich danach noch Code, der es mit meiner App verdrahtet. Dieser Teil gehört in die Historie des Monorepos, denn das ist die Integration.

## `--squash`

`git subtree` bringt auch eine Option mit, die Historie des anderen Repos zu squashen:

```console
git subtree add --squash --prefix=vendor/lib \
  https://git.example.com/lib.git main
```

Allerdings versteht `git subtree` unter `--squash` etwas Eigenartiges. Statt eines einzigen Commits squasht es nur das andere Repository zu einem Commit *q*, und ein Merge-Commit *s* des Monorepos joint ihn ein. Es entstehen also immer zwei Commits statt einem:

![Die Commits a und s des Monorepos in einer Reihe, und q, ein Commit ohne Eltern, als zweiter Elternteil von s](../git-splice/test/comparisons/git-subtree-squash-add.drawio.svg)

Weil dann die Historie fehlt, muss `git subtree` bei jedem Push neu berechnen, welche Commits das andere Repository noch nicht kennt. Wo es anfangen kann, liest `git subtree split` aus den Commit-Nachrichten. `add`, `pull` und `split --rejoin` schreiben Zeilen wie `git-subtree-split: <commit>` hinein. Erst eine Zeile `git-subtree-mainline:` sagt `split`, bis zu welchem Commit es die Historie des Monorepos schon kennt. Ohne `--squash` hat der Merge von `add` diese Zeile, *q* hat sie nicht:

```console
$ git log -1 --format=%B HEAD~4^2 | grep '^git-subtree-'
git-subtree-dir: vendor/lib
git-subtree-split: bafd496b1f4512a95b69464604f3da428aa9e33b
```

Sagen wir, *c* und *e* fixen das Sub-Repository, *b* und *d* ändern die App. Um *c* und *e* zu finden, orange umrandet, durchsucht `git subtree split` auf einmal die gesamte Historie des Monorepos, grau gefüllt. Hier sind das 46 Commits, denn *a* steht für 40 App-Commits, und nur zwei davon zählen:

![Die Commits a, s, b, c, d und e des Monorepos in einer Reihe, und q als zweiter Elternteil von s. Alle sind grau, weil split sie durchläuft, und c und e sind orange umrandet, weil es sie findet](../git-splice/test/comparisons/git-subtree-split-walks.drawio.svg)

Nur mit `--squash` skaliert das nicht.

## `--rejoin`

Dieses Problem soll ein weiteres Flag lösen, `--rejoin`. Damit legt `git subtree` bei jedem Push einen Synchronisationspunkt in der Historie ab, wieder einen gesquashten Commit *r* und einen Merge *j*. Die Nachricht von *j* hat, was *q* fehlt, die Zeile `git-subtree-mainline:`:

```console
$ git log -1 --format=%B | grep '^git-subtree-'
git-subtree-dir: vendor/lib
git-subtree-mainline: 9d3cc6061455cb38432ce9846218e1227e4771be
git-subtree-split: 48108daa0f798109c3e672ed47a7de6204cf4e02
```

Danach durchläuft `split` nur noch die Commits ab dem Synchronisationspunkt. Nach zwei weiteren Commits *g* und *h* sind das fünf:

![Die Commits a, s, b, c, d, e, j, g und h des Monorepos in einer Reihe. Darunter q als zweiter Elternteil von s, und r, auf q aufbauend, als zweiter Elternteil von j. e, r, j, g und h sind grau, weil split sie durchläuft, und h ist orange umrandet, weil es ihn findet](../git-splice/test/comparisons/git-subtree-rejoin-walks.drawio.svg)

Der Preis dafür: Ähnlich wie bei Submodulen entstehen viele Commits, die sich völlig überflüssig anfühlen. Mit `--squash` entstehen zwei Commits beim Pullen, mit `--rejoin` zwei weitere bei jedem Push.

Die Historie sieht entsprechend durcheinander aus. Hier sind es drei Sub-Repositories, zweimal in derselben Reihenfolge gepusht:

![Die Historie des Monorepos mit Merges für drei Sub-Repositories x, y und z, zweimal in derselben Reihenfolge rejoined. Die gesquashten Commits jedes Sub-Repos bilden eine eigene Reihe, und die Pfeile von y und z zu ihren Merges kreuzen die Reihen darüber](../git-splice/test/comparisons/git-subtree-rejoin-three.drawio.svg)

Dieses Muster habe ich gesehen, als ich mein Tool zunächst auf `git subtree` aufgebaut hatte.

Weil die Synchronisationspunkte nur in den Commit-Nachrichten stehen, gehen sie verloren, sobald ein Rewrite Commits zusammenfasst, etwa beim Squash-Merge eines Pull Requests. Dann durchsucht `split` wieder die gesamte Historie.

All das zeigt: `git subtree` ist das falsche Werkzeug, wenn man zwei Repositories mit unterschiedlichen Historien hin und her synchronisieren möchte. Gut geeignet ist es dagegen, wenn man aus zwei Repositories eins machen möchte. Das ist in unserem Anwendungsfall aber nicht so.
