---
slug: was-bei-git-submodulen-schiefgeht
id: submodule-problems
title: "Was bei Git-Submodulen schiefgeht"
description: "Ein git submodule add schreibt an sechs Stellen. Der Commit speichert einen Zeiger, nicht die Änderung, und der Rest ist Zustand, den Klone und Worktrees auf unterschiedliche Weise teilen."
series: why-splicing
seriesOrder: 2
topics: [git]
question: "Habt ihr schon mal Git-Submodule benutzt, und wie war eure Erfahrung damit?"
docs: ../git-splice/test/comparisons/git-submodule.md
---

Die älteste Implementierung von einem Repository, das in einem anderen steckt, heißt `git submodule`. Leider haben `git submodule`s eine ausgesprochen schlechte Reputation. Wir schauen uns mal an, woran das liegt.

Wir nehmen ein Beispiel:

## Wo ein Submodul seinen Zustand ablegt

```console
$ git ls-tree HEAD vendor/lib
160000 commit bafd496b1f4512a95b69464604f3da428aa9e33b vendor/lib
```

Erstens der Commit. Der Tree des Monorepos hat einen Eintrag mit dem Modus 160000, einen sogenannten Gitlink. Er enthält die ID eines Commits der Bibliothek. Nur die ID: Den Commit selbst hat das Monorepo nicht.

```console
$ git ls-files --stage vendor/lib
160000 bafd496b1f4512a95b69464604f3da428aa9e33b 0 vendor/lib
```

Zweitens der Index, die Datei in `.git`, in der Git den nächsten Commit vorbereitet. Er hat denselben Eintrag. Ob sich das Submodul geändert hat, sieht Git nicht an den Dateien der Bibliothek. Es vergleicht den `HEAD` der Bibliothek mit dieser ID.

```console
$ cat .gitmodules
[submodule "vendor/lib"]
 path = vendor/lib
 url = https://git.example.com/lib.git
```

Drittens `.gitmodules`, eine Datei, die wie jede andere committet wird. Sie gibt dem Submodul einen Namen und ordnet dem Namen einen Pfad und eine URL zu.

```console
$ git config --get-regexp '^submodule\.'
submodule.vendor/lib.url https://git.example.com/lib.git
submodule.vendor/lib.active true
```

Viertens die `.git/config` des Monorepos. Git hat die URL hierher kopiert. In einem frischen Klon macht `git submodule init` diese Kopie. Und um die Bibliothek zu klonen, nimmt Git diese Kopie, nicht `.gitmodules`.

```console
$ cat vendor/lib/.git
gitdir: ../../.git/modules/vendor/lib
```

Fünftens der Ordner der Bibliothek. Sein `.git` ist kein Repository, nur eine Datei, die auf eines zeigt.

```console
$ git -C vendor/lib config --get-regexp 'core.worktree|remote.origin.url'
core.worktree ../../../../vendor/lib
remote.origin.url https://git.example.com/lib.git
```

Sechstens das eigene Repository der Bibliothek, versteckt in `.git/modules`. Seine Konfiguration zeigt zurück auf den Ordner. Und sie enthält die URL ein drittes Mal, die, von der es fetcht.

Ich halte zwei Entscheidungen in diesem Design für Fehler, und alles andere folgt daraus.

## Fehler 1: Was zusammengehört, wird getrennt gespeichert

Das Monorepo speichert eine URL und einen Commit der Bibliothek, aber nie die Dateien der Bibliothek. Wenn ich also eine Datei in der Bibliothek und eine in der App ändere, zeigt mir `git status` die Datei der Bibliothek gar nicht. Es meldet nur, dass sich das Submodul geändert hat:

```console
$ git status --short
 M app/main.txt
 m vendor/lib
```

Zum Committen brauche ich zwei Commits in zwei Repositories. Erst den Bugfix *f* in der Bibliothek, dann *b* im Monorepo, der nichts weiter speichert als den neuen Zeiger auf *f*:

![Die Commits a und b des Monorepos in einer Reihe. Darunter die Commits l und f der Bibliothek, jeweils unter dem Monorepo-Commit, der sie speichert](../git-splice/test/comparisons/git-submodule-fix.drawio.svg)

Der Monorepo-Commit *b* enthält die Änderung nicht. Er enthält einen Verweis auf einen Commit, den es in diesem Moment nur auf meinem Rechner gibt. Das hat Folgen:

- `git log -- vendor/lib/src/parse.txt` ist im Monorepo leer. Das Monorepo hat keine Historie der Bibliotheksdateien.
- Ich muss in der richtigen Reihenfolge pushen. Pushe ich zuerst das Monorepo, bekommen meine Kolleginnen und Kollegen einen Commit, den sie nicht auschecken können: `fatal: remote error: upload-pack: not our ref`.
- Bei ihnen steht die Bibliothek auf einem losgelösten `HEAD`. Wer dort etwas fixen will, muss zuerst einen Branch anlegen.

Ein Commit soll eine Momentaufnahme dessen sein, was ich geändert habe. Mit einem Submodul liegt die Hälfte meiner Änderung woanders.

## Fehler 2: Geteilter, veränderlicher Zustand

„Geteilter, veränderlicher Zustand ist die Wurzel allen Übels“ ist eine alte Regel aus der Programmierung, und Submodule laufen direkt hinein.

Die sechs Stellen leben nicht einmal gleich lang. Gitlink und `.gitmodules` werden committet, alle bekommen sie. Der Index, die Zeigerdatei und das Repository der Bibliothek gehören zu einem Worktree. Ich nutze oft `git worktree`, um einen zweiten Branch neben dem ersten ausgecheckt zu haben. In einem neuen Worktree ist das Submodul leer, und es bekommt einen eigenen Klon der Bibliothek unter `.git/worktrees/<name>/modules/`.

Aber die Konfiguration gehört zum Klon, und alle seine Worktrees teilen sie sich. Zeige ich das Submodul in einem Worktree auf meinen Fork, habe ich es in allen geändert:

```console
$ git -C ../feature config submodule.vendor/lib.url https://git.example.com/lib-fork.git
$ git config submodule.vendor/lib.url
https://git.example.com/lib-fork.git
```

Und die Kopien laufen auseinander. Ändert jemand im Team die URL in `.gitmodules`, fetcht mein Klon weiter von der alten, bis ich `git submodule sync` aufrufe. Nichts zeigt mir, welche der Stellen recht hat. Außerdem weigert sich Git, einen Worktree mit Submodulen zu verschieben oder zu entfernen, außer mit `--force`. Die Git-Dokumentation sagt es offen: Die Unterstützung für Submodule ist unvollständig, und mehrere Checkouts eines Superprojects werden ausdrücklich nicht empfohlen.

## Was ich stattdessen will

Die Dateien der Bibliothek sollen im Monorepo-Commit stehen, wie alle anderen Dateien auch. Dann sind der Bugfix und der Code, der ihn aufruft, ein Commit, `status` und `log` sehen jede Datei, und jeder Worktree hat die Bibliothek ohne weitere Einrichtung:

![Die Commits s und c des Monorepos in einer Reihe. Darunter der Commit l der Bibliothek, main zeigt auf l](../git-splice/test/comparisons/git-submodule-splice-fix.drawio.svg)

Hier ändert *c* Bibliothek und App in einem Commit. Die Bibliothek hat noch keinen neuen Commit. Ihr `main` bleibt bei *l*, bis ich mich entscheide, den Bugfix dorthin zu schicken. Wie das funktioniert, darum geht es in dieser Serie.

## Wo Submodule trotzdem besser sind

Submodule haben echte Stärken. Ein Klon ohne `--recurse-submodules` lädt die Bibliothek gar nicht erst herunter. Der Monorepo-Commit legt einen exakten Commit der Bibliothek fest. Und die Bibliothek kann privat bleiben, während das Monorepo öffentlich ist, oder umgekehrt. Wenn diese Punkte am wichtigsten sind, sind Submodule eine vernünftige Wahl.
