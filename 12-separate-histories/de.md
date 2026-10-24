---
slug: vendoring-ohne-historie-zu-importieren
title: "Vendoring braucht keine importierte Historie"
description: "Der Squash-Modus von git subtree versteckt Upstream-Commits, erzeugt aber weiterhin eine Seitenhistorie und einen Merge. Ein vendorter Baum braucht eine Referenz auf den Upstream – keine Upstream-Abstammung."
series: splicing-concepts
seriesOrder: 4
topics: [git]
---

Christophe Porteneuves [Anleitung zu Git-Subtrees](https://medium.com/@porteneuve/mastering-git-subtrees-943d29a798ec) zeigt eine Überraschung von `--squash`: Die importierten Commits werden reduziert, doch `git subtree` pflegt weiterhin einen eigenen Pseudo-Branch und mergt ihn bei jedem Pull. Porteneuve kritisiert, dass dies den Graphen dauerhaft überlädt.

Der Name suggeriert ein lineares Ergebnis: viele Upstream-Commits werden zu einem Monorepo-Commit zusammengefasst. `git subtree pull --squash` erzeugt jedoch etwas anderes.

## Gesquashter Inhalt, nichtlinearer Graph

Gits eigene [Subtree-Dokumentation](https://github.com/git/git/blob/master/contrib/subtree/git-subtree.adoc) beschreibt `--squash` als einen Commit mit allen importierten Unterschieden. Die Implementierung mergt diesen synthetischen Commit anschließend mit `--no-ff`.

Ein Pull fügt deshalb zwei Commits hinzu:

```text
*   M  Merge commit S as 'vendor/parser'
|\
| * S  Squashed 'vendor/parser/' changes from U1..U2
|/
*   A  Vorheriger Monorepo-Commit
```

`S` gehört zu einer synthetischen Seitenhistorie. `M` verbindet sie mit dem Monorepo. Die einzelnen Upstream-Commits fehlen, doch die Monorepo-Historie bleibt nichtlinear.

Diese Form ist kein zufälliges Bookkeeping. Spätere `git subtree`-Befehle suchen darin den früheren Upstream-Punkt. Entfernt ein Rebase oder Squash-Merge den zweiten Parent, können die Dateien erhalten bleiben, während ihre Beziehung zum Upstream verschwindet.

Diese Kritik traf meinen Eindruck: `git subtree` verlangt überraschende Historie als Preis dafür, dass vendorter Code wie normale Dateien behandelt werden kann. Ich hatte die Befehle automatisiert, aber die Automatisierung entfernte diese Kopplung nicht.

## Welche Historie muss welches Repository erklären?

Der Wendepunkt war, zwei Fragen zu trennen.

Die Monorepo-Historie soll erklären:

- wann sich ihre Kopie von `vendor/parser` änderte;
- welche anderen Monorepo-Änderungen gemeinsam ausgeliefert wurden;
- welchem Upstream-Stand diese Kopie entspricht.

Die Parser-Historie soll erklären:

- wie sich der Parser als eigenständiges Projekt entwickelte;
- welche Monorepo-Änderungen zurück veröffentlicht wurden;
- welche Autorenschaft und Reihenfolge sie in Parser-Pfaden haben.

Keines der beiden Repositories braucht die Commits des anderen als Vorfahren.

Für Vendoring genügt ein gewöhnlicher Monorepo-Commit plus eingecheckte Upstream-ID:

```text
* P  splice: pull vendor/parser to 206f2a2
* A  Vorheriger Monorepo-Commit
```

`P` ändert den Ordner und seine `.splice`-Datei gemeinsam. Die Datei hält fest, welcher Upstream-Baum integriert wurde. Gefetchte Upstream-Commits können für Merges und Inspektion unter privaten Refs liegen, ohne Vorfahren des Monorepo-Branches zu werden.

## Für den Push lässt sich die andere Sicht rekonstruieren

Lokale Monorepo-Commits müssen im Upstream weiterhin sinnvolle Commits werden. Dafür muss die rekonstruierte Historie nicht im Monorepo-Graph gespeichert werden.

Git Splice durchläuft ab der gespeicherten Grenze jene Commits, die den Ordner berührt haben. Für jeden schreibt es den Ordner als Root-Baum, entfernt `.splice`, ordnet Parents zu und bewahrt Autor, Committer, Zeitpunkte und Nachricht. Das Ergebnis ist eine deterministische Upstream-Historie, die direkt gepusht werden kann.

Diese Commits sind eine Projektion der Monorepo-Historie, keine Vorfahren, die das Monorepo dauerhaft behalten muss. Private Refs können sie halten; bei Bedarf lassen sie sich reproduzieren.

Diese Trennung klärte den Entwurf stärker als jede Optimierung: Synchronisation braucht eine überprüfbare Entsprechung zwischen zwei Historien, nicht eine gemeinsame Historie. Sobald der Commit-Graph nicht mehr beide Repositories gleichzeitig darstellen musste, wurden Pulls zu gewöhnlichen Commits und Vendoring schrieb dem Monorepo keine Merge-Topologie mehr vor.
