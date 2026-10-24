---
slug: git-submodules
title: "Git Submodules"
description: "Ein git submodule add schreibt an sechs Stellen. Der Commit speichert einen Zeiger, nicht die Änderung, und der Rest ist Zustand, den Klone und Worktrees auf unterschiedliche Weise teilen."
series: why-splicing
seriesOrder: 2
topics: [git]
question: "Habt ihr schon mal Git-Submodule benutzt, und wie war eure Erfahrung damit?"
docs: ../git-splice/test/comparisons/git-submodule.md
---

Git hat eine eigene Implementierung von verschachtelten Repositories: Submodule.

„Submodul“ – das klingt nach dem richtigen Konzept. Aber leider ist die Anwendung ziemlich fehleranfällig. Wir schauen uns mal an, woran das liegt. Also bauen wir uns mal ein Beispiel:

```console
# roschaefer.github.io/git-splice/docs/sandbox
git clone https://github.com/roschaefer/git-splice.git
cd git-splice
nix develop -c just sandbox comparisons/git-submodule
```

Übrigens: Ihr könnt das Beispiel selbst ausführen. Diese Befehle öffnen eine Sandbox mit dem Submodul und dem Monorepo, und jeder Befehl gibt aus, was ihr hier seht. Wie das geht, steht in der [Dokumentation von git-splice](https://roschaefer.github.io/git-splice/docs/sandbox/#any-page-in-a-sandbox).

Das Beispiel baut ein Monorepo und ein weiteres Repository mit 30 Commits. Danach fügen wir das andere Repository als Submodul zum Monorepo hinzu. Dieser eine Befehl, `git submodule add`, schreibt an insgesamt sechs Stellen:

```console
git submodule add https://git.example.com/lib.git vendor/lib
```

Jetzt committen wir das Submodul im Monorepo:

```console
git commit -m "add lib as a submodule"
```

## Wo ein Submodul seinen Zustand ablegt

```text
monorepo/
├── .gitmodules      Name, Pfad und URL
├── app/
│   └── main.txt
└── vendor/
    └── lib          Gitlink: 160000 commit bafd496
```

- Im Commit des Monorepos steht am Ordnerpfad des Submoduls nur ein sogenannter Gitlink mit der ID des ausgecheckten Commits des Submoduls. Den Commit selbst speichert das Monorepo nicht.

- Im Wurzelverzeichnis befindet sich eine weitere Datei, die `.gitmodules`. Sie gibt dem Submodul einen Namen, speichert den Ordnerpfad zum Submodul sowie die Upstream-URL, ähnlich wie bei einem `git remote`.

Außerdem gibt es noch [vier weitere Stellen](https://roschaefer.github.io/git-splice/test/comparisons/git-submodule/#where-a-submodule-keeps-its-state), an denen Git ein Submodul ablegt. Aber nur die beiden oben genannten landen im Commit.

## Fehler 1: Was zusammengehört, wird getrennt gespeichert

Weil das Monorepo nur die Commit-ID des Submoduls speichert, sieht es die Dateien des Submoduls nicht. Wenn ich zum Beispiel eine Datei innerhalb und eine außerhalb des Submoduls ändere:

```console
echo "fix" >>vendor/lib/src/parse.txt
echo "call parse()" >>app/main.txt
```

Dann zeigt mir `git status` die Änderungen innerhalb des Submoduls gar nicht an. Es meldet nur, dass sich der Zeiger auf das Submodul geändert hat:

```console
$ git status --short
 M app/main.txt
 m vendor/lib
```

Für diese eine Änderung brauche ich zwei Commits in zwei Repositories. Erst den Bugfix *f* im Submodul, dann *b* im Monorepo, der nichts weiter speichert als den neuen Zeiger auf *f*:

![Die Commits a und b des Monorepos in einer Reihe. Darunter die Commits l und f des Submoduls, jeweils unter dem Monorepo-Commit, der sie speichert](../git-splice/test/comparisons/git-submodule-fix.drawio.svg)

Das hat Folgen. Ich kann zum Beispiel das Monorepo pushen und den dazugehörigen Commit vom Submodul vergessen. Dann bekommen meine Kollegen beim Klonen einen Fehler:

```console
$ git clone --recurse-submodules ../origin.git ../colleague
fatal: remote error: upload-pack: not our ref a6152f5cee8b2bfd6b5dfc7bbb2bf5d8a7562325
```

Auch andere Befehle wie `git log` schauen nicht über die Grenze des Submoduls, weil das Monorepo nur den Zeiger kennt. Die Historie einer Datei im Submodul ist im Monorepo leer:

```console
git log --oneline -- vendor/lib/src/parse.txt
```

Und warum steht der Pfad des Submoduls noch einmal in `.gitmodules`? Der Gitlink liegt doch schon an diesem Pfad:

```text
monorepo/
├── .gitmodules      Pfad: vendor/lib
├── app/
│   └── main.txt
└── vendor/
    └── lib          Hier ist der Pfad implizit
```

## Fehler 2: „Geteilter, veränderlicher Zustand ist die Wurzel allen Übels“

„Geteilter, veränderlicher Zustand ist die Wurzel allen Übels“ – das ist eine bekannte Falle in der Programmierung, und Submodule laufen direkt hinein.

Submodule legen auch globalen Zustand außerhalb des Worktrees ab, zum Beispiel in der `.git/config` des Monorepos. Diese Datei teilen sich alle Worktrees. Ich nutze oft mehrere Worktrees, um parallel zu arbeiten. Ändere ich in einem Worktree die Konfiguration, zum Beispiel die Upstream-URL, dann habe ich sie *in allen Worktrees* geändert:

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

Sollte das Monorepo nicht alles mit sich tragen, was es zum Leben braucht? Warum liegt der Zustand eines Submoduls an so vielen verschiedenen Stellen verstreut? Die Dateien des Submoduls könnten doch im Monorepo-Commit stehen, so wie alle anderen Dateien.

Aus dem Monorepo heraus könnte man mit einem einzigen Commit *c* die Dateien des Submoduls und die des Monorepos simultan ändern:

![Die Commits s und c des Monorepos in einer Reihe. Darunter der Commit l der Bibliothek, main zeigt auf l](../git-splice/test/comparisons/git-submodule-splice-fix.drawio.svg)

Erst wenn ich mich entscheide, den Bugfix zum Repository des Submoduls zu übertragen, würde ich einen Commit dorthin schicken.
