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

`git subtree` macht den ersten Teil richtig. Es legt die Dateien eines anderen Repositorys in einen Ordner des Monorepos. Ein Fix im Sub-Repository und der Code, der ihn aufruft, können also ein Commit sein. `git subtree split` und `git subtree push` machen aus den Monorepo-Commits, die den Ordner geändert haben, wieder Commits des Sub-Repositorys.

git-splice hat als Wrapper um `git subtree` angefangen. Ich habe es aufgegeben, weil man damit keine lineare Historie bekommt. Es gibt drei Wege, und keiner führt dahin.

## Ohne `--squash`: die ganze Historie des Sub-Repositorys

Ohne `--squash` merged `git subtree add` alle Commits des Sub-Repositorys ins Monorepo. In meinem Testaufbau hat ein Monorepo mit 40 Commits danach 71, weil das Sub-Repository 30 Commits mitbringt.

Das Monorepo nutzt das Sub-Repository. Es entwickelt nicht dessen Vergangenheit weiter. Die Änderungen, die das Monorepo interessieren, also die, die das Sub-Repository in die App einpassen, sind ohnehin Monorepo-Commits.

## Nur `--squash`: skaliert nicht

`--squash` hält die Historie des Sub-Repositorys draußen. `add` erzeugt einen Commit *q* mit den Dateien des Sub-Repositorys und ohne Eltern und merged ihn als *s*:

![Die Commits a und s des Monorepos in einer Reihe, und q, ein Commit ohne Eltern, als zweiter Elternteil von s](../git-splice/test/comparisons/git-subtree-squash-add.drawio.svg)

Dann arbeite ich. *c* und *e* fixen das Sub-Repository, *b* und *d* ändern die App:

![Die Commits a, s, b, c, d und e des Monorepos in einer Reihe, und q als zweiter Elternteil von s](../git-splice/test/comparisons/git-subtree-squashed.drawio.svg)

Um die beiden Fixes zu pushen, muss `split` herausfinden, welche Commits das Sub-Repository geändert haben. Mit `--squash` enthält das Monorepo keinen Commit des Sub-Repositorys, bei dem es anfangen könnte. Also durchläuft `split` die ganze Historie des Monorepos, bei jedem Push. In meinem Aufbau sind das 46 Commits, obwohl nur zwei davon zählen. In einem Monorepo mit Jahren an Historie wird das langsam.

## `--squash` und `--rejoin`: eine hässliche Historie

Das Beste, was man machen kann: `split --rejoin` merged das Ergebnis als neuen Startpunkt zurück. Das ist ein weiterer Merge *j* bei jedem Push, mit einem weiteren gesquashten Commit *r* auf *q*:

![Die Commits a, s, b, c, d, e und j des Monorepos in einer Reihe. Darunter q als zweiter Elternteil von s, und r, auf q aufbauend, als zweiter Elternteil von j](../git-splice/test/comparisons/git-subtree-rejoin.drawio.svg)

Und es geht kaputt, sobald Pull Requests per Squash gemerged werden, was verbreitet ist. Der Squash-Merge behält die Fixes, verwirft aber *j* und *r*. Der nächste `split` durchläuft also wieder alles:

![Die Commits a, s und p des Monorepos in einer Reihe, und q als zweiter Elternteil von s](../git-splice/test/comparisons/git-subtree-squash-merged.drawio.svg)

Mit einem Sub-Repository ist der Graph noch lesbar. Mit drei bringt jedes Sub-Repository seine eigenen gesquashten Commits und seine eigenen Merges mit. Rejoine ich sie immer in derselben Reihenfolge, entsteht bei jedem Rejoin dasselbe Muster, eine Treppe aus Pfeilen, die sich kreuzen:

![Die Historie des Monorepos mit Merges für drei Sub-Repositorys x, y und z, zweimal in derselben Reihenfolge rejoined. Die gesquashten Commits jedes Sub-Repositorys bilden eine eigene Reihe, und die Pfeile von y und z zu ihren Merges kreuzen die Reihen darüber](../git-splice/test/comparisons/git-subtree-rejoin-three.drawio.svg)

Keiner dieser Merges sagt etwas über die App. Sie sind nur da, damit `split` schnell ist.

## Wo `git subtree` das richtige Werkzeug ist

Wer ein Repository endgültig in ein Monorepo umzieht und das alte stilllegt, ist mit `git subtree add` ohne `--squash` genau richtig. Die Historie kommt mit, und `git blame` funktioniert weiter.

## Was ich mitgenommen habe

Ich wollte die Dateien des Sub-Repositorys im Monorepo haben, mit einer linearen Historie: ohne die Historie des Sub-Repositorys, ohne Merges, die nur dafür da sind, dass Pushen schnell geht, und mit einem Push, der nur ansieht, was sich seit dem letzten Abgleich geändert hat. Die nächsten Folgen zeigen, wie das zusammenpasst.
