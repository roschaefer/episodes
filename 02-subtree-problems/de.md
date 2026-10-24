---
slug: was-bei-git-subtree-schiefgeht
title: "Was bei git subtree schiefgeht"
description: "git subtree importiert entweder die ganze Historie der Bibliothek oder durchläuft bei jedem Push die ganze Historie des Monorepos. Und ein Remote pro Bibliothek ist einen Tippfehler davon entfernt, das Monorepo zu veröffentlichen."
series: why-splicing
seriesOrder: 3
topics: [git]
question: "Habt ihr schon mal Git-Subtrees benutzt, um eine Bibliothek zu vendoren?"
docs: ../git-splice/test/comparisons/git-subtree.md
---

`git subtree` macht den ersten Teil richtig. Es legt die Dateien der Bibliothek in einen Ordner des Monorepos. Ein Fix in der Bibliothek und der Code, der ihn aufruft, können also ein Commit sein. `git subtree split` und `git subtree push` machen aus den Monorepo-Commits, die den Ordner geändert haben, wieder Commits der Bibliothek.

git-splice hat als Wrapper um `git subtree` angefangen. Aus drei Gründen habe ich es aufgegeben.

## Grund 1: Ich will die Historie der Bibliothek nicht

Ohne `--squash` merged `git subtree add` alle Commits der Bibliothek ins Monorepo. In meinem Testaufbau hat ein Monorepo mit 40 Commits danach 71, weil die Bibliothek 30 Commits mitbringt.

Das Monorepo nutzt die Bibliothek. Es entwickelt nicht ihre Vergangenheit weiter. Die Änderungen, die das Monorepo interessieren, also die, die die Bibliothek in die App einpassen, sind ohnehin Monorepo-Commits.

## Grund 2: Mit `--squash` skaliert es nicht

`--squash` hält die Historie der Bibliothek draußen. `add` erzeugt einen Commit *q* mit den Dateien der Bibliothek und ohne Eltern und merged ihn als *s*:

![Die Commits a und s des Monorepos in einer Reihe, und q, ein Commit ohne Eltern, als zweiter Elternteil von s](../git-splice/test/comparisons/git-subtree-squash-add.drawio.svg)

Dann arbeite ich. *c* und *e* fixen die Bibliothek, *b* und *d* ändern die App:

![Die Commits a, s, b, c, d und e des Monorepos in einer Reihe, und q als zweiter Elternteil von s](../git-splice/test/comparisons/git-subtree-squashed.drawio.svg)

Um die beiden Fixes zu pushen, muss `split` herausfinden, welche Commits die Bibliothek geändert haben. Mit `--squash` enthält das Monorepo keinen Commit der Bibliothek, bei dem es anfangen könnte. Also durchläuft `split` die ganze Historie des Monorepos, bei jedem Push. In meinem Aufbau sind das 46 Commits, obwohl nur zwei davon zählen. In einem Monorepo mit Jahren an Historie wird das langsam.

`split --rejoin` hilft, indem es das Ergebnis als neuen Startpunkt zurück merged. Das ist ein weiterer Merge *j* bei jedem Push, mit einem weiteren gesquashten Commit *r* auf *q*:

![Die Commits a, s, b, c, d, e und j des Monorepos in einer Reihe. Darunter q als zweiter Elternteil von s, und r, auf q aufbauend, als zweiter Elternteil von j](../git-splice/test/comparisons/git-subtree-rejoin.drawio.svg)

Und es geht kaputt, sobald Pull Requests per Squash gemerged werden, was verbreitet ist. Der Squash-Merge behält die Fixes, verwirft aber *j* und *r*. Der nächste `split` durchläuft also wieder alles:

![Die Commits a, s und p des Monorepos in einer Reihe, und q als zweiter Elternteil von s](../git-splice/test/comparisons/git-subtree-squash-merged.drawio.svg)

Mit einer Bibliothek ist der Graph noch lesbar. Mit drei bringt jede Bibliothek ihre eigenen gesquashten Commits und ihre eigenen Merges mit, und ihre Pfeile kreuzen sich:

![Die Historie des Monorepos mit Merges für drei Bibliotheken. Die gesquashten Commits jeder Bibliothek bilden eine eigene Reihe, und die Pfeile von Bibliothek B und C zu ihren Merges kreuzen die Reihen der anderen Bibliotheken](git-subtree-rejoin-three-libraries.drawio.svg)

Keiner dieser Merges sagt etwas über die App. Sie sind nur da, damit `split` schnell ist.

## Grund 3: Ein Remote pro Bibliothek ist einen Tippfehler davon entfernt, das Monorepo zu veröffentlichen

`git subtree push` braucht ein Remote oder jedes Mal eine URL. Mein Wrapper hat pro Bibliothek ein Git-Remote angelegt und es wie den Ordner benannt. Das sieht aufgeräumt aus, bis man `git push vendor/lib main` tippt statt `git subtree push --prefix=vendor/lib vendor/lib main`. Dann landet das ganze Monorepo im Repository der Bibliothek, samt Ordnern, die es nie verlassen sollten.

Dafür braucht es nicht einmal einen Tippfehler. Ein einfaches `git push` mit `push.autoSetupRemote`, der Sync-Knopf einer IDE oder eine Suche in der Shell-Historie können dasselbe anrichten. Den Branch danach zu löschen, macht nichts ungeschehen. Dazu gibt es eine eigene Folge.

## Wo `git subtree` das richtige Werkzeug ist

Wer ein Repository endgültig in ein Monorepo umzieht und das alte stilllegt, ist mit `git subtree add` ohne `--squash` genau richtig. Die Historie kommt mit, und `git blame` funktioniert weiter.

## Was ich mitgenommen habe

Ich wollte die Dateien der Bibliothek im Monorepo haben, ohne ihre Historie, ohne Merges, die nur dafür da sind, dass Pushen schnell geht, mit einem Push, der nur ansieht, was sich seit dem letzten Abgleich geändert hat, und ohne ein Git-Remote pro Bibliothek. Die nächsten Folgen zeigen, wie das zusammenpasst.
