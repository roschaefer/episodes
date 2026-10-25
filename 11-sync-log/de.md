---
title: "Mit Synchronisationszustand wird der Log trivial"
description: "Eine eingecheckte Grenze macht aus den Fragen ‚Was wird gepusht?‘ und ‚Was wird gepullt?‘ gewöhnliche Mengenoperationen auf Git-Historien."
topics: [git]
---

[Issue #51](https://github.com/roschaefer/git-subtrees/issues/51) begann als überschaubarer UX-Wunsch: Vor dem Push eines Ordners sollten die Commits sichtbar sein, die veröffentlicht werden.

`git subtrees diff` zeigte Dateiänderungen, doch ein Push veröffentlicht Commits. Ihre Nachrichten können für ein privates Monorepo-Publikum geschrieben worden sein. Identitäten von Autor und Committer werden öffentlich. Beim Anlegen eines neuen Upstream-Branches können viel mehr Commits als erwartet erscheinen. Ein finaler Diff verbirgt all das.

Im alten Entwurf erforderte die Antwort zuerst die teure Operation aus Issue #30: `git subtree split` musste die Ordnerhistorie rekonstruieren, bevor sie mit Remote-Tracking-Branches verglichen werden konnte. Das Feature wirkte klein, hing aber vom langsamsten und kompliziertesten Teil des Systems ab.

Der Zustand in `.splice` änderte das.

## Zwei Historien mit bekannter Verbindung

`U` sei der in `.splice` gespeicherte Upstream-Commit. Ab der entsprechenden lokalen Grenze baut Git Splice die späteren Ordner-Commits deterministisch neu auf. Die rekonstruierte Spitze nennen wir `R`.

Nach dem Fetch des Ziel-Branches in einen privaten Ref sind beide Seiten gewöhnliche Git-Historien:

```text
lokal rekonstruiert:  U -- L1 -- L2   (R)
                                \
gefetchter Upstream:  U -- X1 -- X2   (remote)
```

Ein Subtree-spezifischer Log-Algorithmus ist nicht mehr nötig. Git kann Commit-Mengen bereits subtrahieren und vergleichen.

## Ausgehend und eingehend

Ein Push veröffentlicht alles, was von `R`, aber nicht vom gefetchten Branch erreichbar ist:

```sh
git log R --not refs/splices/<path>/<branch>
```

Ein Pull bringt die umgekehrte Menge:

```sh
git log refs/splices/<path>/<branch> --not R
```

Beide Richtungen lassen sich gemeinsam anzeigen:

```sh
git log --left-right --cherry-mark --oneline \
  R...refs/splices/<path>/<branch>
```

`<` und `>` kennzeichnen die Seite. `=` markiert äquivalente Patches. Das ist wichtig, wenn eine Seite eine Änderung cherry-pickt oder rebased und ihr dadurch eine andere Commit-ID gibt.

Existiert der Upstream-Branch noch nicht, lautet die Frage: Welche rekonstruierten Commits fehlen auf allen gefetchten Branches?

```sh
git log R --not --glob='refs/splices/<path>/*'
```

Mit `--stat` erscheinen die Pfade so, wie der Upstream sie sehen wird, denn die rekonstruierten Commits tragen den Ordner bereits an ihrer Wurzel. Ein eigenes Format kann Autor- und Committer-Identitäten vor der Veröffentlichung sichtbar machen.

## Der Befehl wurde zur Konsequenz

Interessant ist nicht nur die Kürze dieser Befehle. Entscheidend ist, dass das sichtbare Feature keine besondere Herleitung mehr braucht.

In `git-subtrees` mussten `status`, `diff`, `pull`, `push` und der geplante `log` jeweils einen Teil der Beziehung aus konfigurierten Remotes und synthetischer Merge-Historie rekonstruieren. Mit eingechecktem Upstream-Zustand und deterministischer lokaler Projektion arbeiten alle auf denselben beiden Spitzen.

Nach solcher Vereinfachung suche ich bei einem Redesign: Eine gute Grundlage macht nicht nur eine Funktion leichter. Mehrere Funktionen folgen direkt aus dem Modell.

Die fertige `log`-Oberfläche darf weiterhin eigene Entscheidungen treffen: standardmäßig alle Splices betrachten, nach Ordner gruppieren, Richtungen markieren und vertraute `git log`-Formate akzeptieren. Darunter vergleicht Git lediglich zwei Historien, deren Verbindung nicht länger versteckt ist.
