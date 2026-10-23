---
slug: git-submodules
id: submodule-problems
title: "git submodules"
description: "Ein git submodule add schreibt an sechs Stellen. Der Commit speichert einen Zeiger, nicht die Änderung, und der Rest ist Zustand, den Klone und Worktrees auf unterschiedliche Weise teilen."
series: why-splicing
seriesOrder: 2
topics: [git]
question: "Habt ihr schon mal Git-Submodule benutzt, und wie war eure Erfahrung damit?"
docs: ../git-splice/test/comparisons/git-submodule.md
---

Git hat eine eigene Implementierung von verschachtelten Repositories, sie heißt `git submodule`. Leider haben Submodule eine ausgesprochen schlechte Reputation. Wir schauen uns mal an, woran das liegt.

Wir bauen uns ein Beispiel.

```console
# roschaefer.github.io/git-splice/docs/sandbox
git clone https://github.com/roschaefer/git-splice.git
cd git-splice
nix develop -c just sandbox comparisons/git-submodule
```

Ihr könnt das Beispiel selbst ausführen: Diese Befehle öffnen eine Sandbox mit der Bibliothek und dem Monorepo, und jeder Befehl gibt dort aus, was ihr hier seht. Wie das geht, steht in der [Dokumentation von git-splice](https://roschaefer.github.io/git-splice/docs/sandbox/#any-page-in-a-sandbox).

Das Beispiel baut eine Bibliothek mit 30 Commits und ein Monorepo mit einer App.

Dann fügen wir die Bibliothek als Submodul zum Monorepo hinzu. Dieser eine Befehl, `git submodule add`, schreibt an sechs Stellen:

```console
git submodule add https://git.example.com/lib.git vendor/lib
```

Danach committen wir das Submodul:

```console
git commit -m "add lib as a submodule"
```

## Wo ein Submodul seinen Zustand ablegt

```text
monorepo/
├── .gitmodules      2  Name, Pfad und URL
├── app/
│   └── main.txt
└── vendor/
    └── lib          1  Gitlink: 160000 commit bafd496
```

1. Der Gitlink. Wo die Bibliothek liegt, steht im Commit des Monorepos nur die ID ihres ausgecheckten Commits. Den Commit selbst speichert das Monorepo nicht.

2. `.gitmodules`, eine Datei, die wie jede andere committet wird. Sie gibt dem Submodul einen Namen und ordnet ihm einen Pfad und eine Upstream-URL zu.

Außerdem gibt es noch [vier weitere Stellen](https://roschaefer.github.io/git-splice/test/comparisons/git-submodule/#where-a-submodule-keeps-its-state) außerhalb des Commits, an denen Git ein Submodul ablegt.

## Fehler 1: Was zusammengehört, wird getrennt gespeichert

Weil das Monorepo nur die ID speichert, sieht es die Dateien der Bibliothek nicht. Wenn ich also eine Datei in der Bibliothek und eine in der App ändere, zeigt mir `git status` die Datei der Bibliothek gar nicht. Es meldet nur, dass sich der Zeiger auf das Submodul geändert hat:

```console
$ git status --short
 M app/main.txt
 m vendor/lib
```

Für diese eine Änderung brauche ich zwei Commits in zwei Repositories, und der zweite fühlt sich überflüssig an. Erst den Bugfix *f* in der Bibliothek, dann *b* im Monorepo, der nichts weiter speichert als den neuen Zeiger auf *f*:

![Die Commits a und b des Monorepos in einer Reihe. Darunter die Commits l und f der Bibliothek, jeweils unter dem Monorepo-Commit, der sie speichert](../git-splice/test/comparisons/git-submodule-fix.drawio.svg)

Das hat Folgen. Ich kann zum Beispiel das Monorepo pushen und den dazugehörigen Commit der Bibliothek vergessen. Dann bekommen meine Kollegen beim Klonen einen Fehler:

```console
$ git clone --recurse-submodules ../origin.git ../colleague
fatal: remote error: upload-pack: not our ref a6152f5cee8b2bfd6b5dfc7bbb2bf5d8a7562325
```

Auch andere Befehle wie `git log` schauen nicht über die Grenze des Submoduls, weil das Monorepo nur den Zeiger kennt. Die Historie einer Datei der Bibliothek ist im Monorepo leer:

```console
git log --oneline -- vendor/lib/src/parse.txt
```

```console
$ git ls-tree HEAD vendor/lib
160000 commit a6152f5cee8b2bfd6b5dfc7bbb2bf5d8a7562325	vendor/lib
$ cat .gitmodules
[submodule "vendor/lib"]
	path = vendor/lib
	url = https://git.example.com/lib.git
```

Und warum steht der Pfad des Submoduls noch einmal in `.gitmodules`? Der Gitlink liegt doch schon an diesem Pfad.

## Fehler 2: „Geteilter, veränderlicher Zustand ist die Wurzel allen Übels“

Das ist eine alte Weisheit aus der Programmierung, und Submodule laufen direkt hinein.

Submodule legen auch Zustand außerhalb des Worktrees ab, zum Beispiel in der `.git/config` des Monorepos. Diese Datei teilen sich alle Worktrees. Ich nutze oft mehrere Worktrees, um parallel zu arbeiten. Ändere ich in einem Worktree die Konfiguration, zum Beispiel die Upstream-URL, dann habe ich sie *in allen Worktrees* geändert:

```console
$ git -C ../feature config submodule.vendor/lib.url https://git.example.com/lib-fork.git
$ git config submodule.vendor/lib.url
https://git.example.com/lib-fork.git
```

Ein klassischer Fall von geteiltem, veränderlichem Zustand. Laut Git-Dokumentation ist die Unterstützung für Submodule in Worktrees unvollständig. Wer es trotzdem versucht und einen Worktree mit Submodulen wieder entfernen will, bekommt eine gruselige Fehlermeldung:

```console
$ git worktree remove ../feature
fatal: working trees containing submodules cannot be moved or removed
```

## Was ich stattdessen will

Sollte das Monorepo nicht alles mit sich tragen, was es zum Leben braucht? Warum liegt der Zustand eines Submoduls an so vielen verschiedenen Stellen? Die Dateien der Bibliothek könnten im Monorepo-Commit stehen wie alle anderen Dateien, und eine einzige Datei im Ordner der Bibliothek würde reichen, um sich ihre Herkunft zu merken.

Dann ändert ein einziger Commit *c* Bibliothek und App:

![Die Commits s und c des Monorepos in einer Reihe. Darunter der Commit l der Bibliothek, main zeigt auf l](../git-splice/test/comparisons/git-submodule-splice-fix.drawio.svg)

Die Bibliothek hat noch keinen neuen Commit. Ihr `main` bleibt bei *l*, bis ich mich entscheide, den Bugfix dorthin zu schicken.
