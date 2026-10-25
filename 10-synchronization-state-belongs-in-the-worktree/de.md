---
title: "Synchronisationszustand gehört in den Working Tree"
description: "Historie kann einen Synchronisationspunkt markieren, doch gewöhnliches Umschreiben kann ihn löschen. Eine kleine eingecheckte Zustandsdatei überlebt und ermöglicht inkrementelle Arbeit."
topics: [git]
---

Um einen Ordner zu synchronisieren, muss ein Werkzeug wissen, wo die vorherige Synchronisation endete. Mein erster Entwurf überließ diese Frage `git subtree`.

Ein Squash-Pull schreibt Trailer wie `git-subtree-dir` und `git-subtree-split` in Commits. Spätere Befehle durchsuchen die Historie nach diesen Markern. Das spart eine zusätzliche Datei, macht aber eine bestimmte Form des Commit-Graphen zur Datenbank.

Diese Datenbank ist in meinem Workflow nicht stabil.

## Ein Squash-Merge löschte die Antwort

Ich reproduzierte einen alltäglichen Ablauf:

1. eine Upstream-Änderung auf einem Feature-Branch pullen;
2. denselben Ordner lokal ändern;
3. den Pull Request per Squash in `main` mergen;
4. `git-subtrees` nach dem Zustand fragen.

Der Squash-Merge bewahrte die Dateien, nicht aber den Synchronisations-Commit. `git-subtrees` meldete `diverged`, obwohl der Ordner lediglich die Upstream-Version plus eine lokale Änderung enthielt. Ein Pull zur Wiederherstellung konnte anschließend dazu führen, dass derselbe Upstream-Commit doppelt exportiert wurde.

Die Dateien überlebten. Die an den verworfenen Graphen gebundene Bedeutung nicht.

## Exakte Klassifikation wurde immer teurer

Ein Teil des fragilen Bookkeepings war bereits verschwunden: Für einen exakten Status baute `git subtree split` die Upstream-förmige Historie neu auf und verglich ihre Abstammung mit dem Remote-Branch.

Dadurch entstand [Issue #30](https://github.com/roschaefer/git-subtrees/issues/30). `git subtree split` durchläuft jeden von `HEAD` erreichbaren Commit, auch wenn dieser den Ordner nie berührt hat. In einem Monorepo mit 670 Commits erhöhten zwei lokal veränderte Ordner die Laufzeit von `status` von 0,15 auf 2,86 Sekunden. Synthetische Tests erreichten bei 5.500 Commits 44 Sekunden.

Die wiederkehrenden Kosten wuchsen mit dem Alter des Monorepos statt mit der Arbeit seit der letzten Synchronisation.

`git subtree split --rejoin` kann einen Checkpoint hinzufügen. Dieser ist jedoch ein weiterer Merge in der Historie und kann durch Rebase oder Squash-Merge erneut verschwinden. Ein Cache unter `.git` wäre schneller, reist aber nicht mit einem Clone oder Branch.

## Zustand einchecken, nicht die Graphform

Git Splice legt eine kleine `.splice`-Datei in jeden synchronisierten Ordner. Sie enthält nur Fakten der Upstream-Seite:

```ini
[splice]
url = git@github.com:example/parser.git
commit = 206f2a2...
default-branch = main
```

`commit` ist der Upstream-Commit, dessen Baum zuletzt dem Ordner entsprach. Die Datei enthält absichtlich keine SHA aus dem Monorepo.

Die lokale Grenze lässt sich ableiten: Es ist der neueste Commit der aktuellen Historie, der `.splice` geändert hat. Ein Rebase kann diesem Commit eine neue ID geben. Ein Squash-Merge kann ihn mit lokalen Änderungen verbinden. In beiden Fällen enthält die aktuelle Historie weiterhin den Moment, in dem der gespeicherte Upstream-Zustand in den Ordner kam.

Ab dieser Grenze verarbeitet der Neuaufbau für einen Push nur spätere Commits, die den Ordner berührten. Die Kosten folgen nun der neuen Arbeit statt dem gesamten Repository-Alter.

## Warum die Datei im Ordner liegt

Die Nähe zum Inhalt hat praktische Folgen:

- `git mv` verschiebt Inhalt und Konfiguration gemeinsam;
- ein frischer Clone findet Splices mit `git ls-files`;
- Branches tragen den Zustand ihrer jeweiligen Ordner-Version;
- ein Pull aktualisiert Inhalt und Zustand in einem Commit.

Beim Export entfernt Git Splice `.splice` aus dem rekonstruierten Baum. Sie ist Koordinationsinformation des Monorepos und kein Bestandteil des Upstream-Projekts.

Eingecheckter Zustand ist nicht automatisch dauerhaft. Auch `git-subrepo` speichert Zustand, doch sein Feld `parent` enthält eine Monorepo-SHA, die Rebase und Squash-Merge ungültig machen können. Die entscheidende Wahl lautet nicht nur „Datei oder Historie“. Man sollte ausschließlich stabile Fakten speichern und Identitäten aus umschreibbarer Historie ableiten.
