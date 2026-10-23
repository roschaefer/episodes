---
slug: teile-eines-monorepos-unabhaengig-veroeffentlichen
id: motivation
title: "Teile eines Monorepos unabhängig veröffentlichen"
description: "Ein Ordner soll im Monorepo entwickelt und zugleich als eigenständiges Repository veröffentlicht werden. Git bietet dafür Submodule und Subtrees – mit sehr unterschiedlichen Nachteilen."
series: why-splicing
seriesOrder: 4
topics: [git]
---

Ein Monorepo ist praktisch, solange alles darin gemeinsam entwickelt werden darf. Doch nicht alles darin soll auch gemeinsam veröffentlicht werden. Vielleicht enthält es mehrere Werkzeuge, von denen nur einige Open Source sind. Intuitiv liegt jedes öffentliche Projekt in einem Unterordner, der zusätzlich als eigenständiges Repository auf GitHub erscheint.

Ein einmaliger Export reicht nicht. Abhängigkeiten werden im öffentlichen Repository aktualisiert, andere Menschen tragen Änderungen bei, und diese Arbeit muss zurück ins Monorepo. Gleichzeitig entstehen neue Features weiterhin zusammen mit dem übrigen System und sollen von dort veröffentlicht werden. Der Ordner braucht eine bidirektionale Synchronisation.

Das gleiche Problem tritt beim Vendoring aus der anderen Richtung auf. Eine Anwendung braucht eine Änderung an einer Bibliothek, kann aber nicht auf deren nächste Veröffentlichung warten. Das Team nimmt den Quellcode ins Monorepo auf, entwickelt und testet den Patch zusammen mit der Anwendung und möchte ihn anschließend upstream beitragen. Da ihm das Ursprungsrepository nicht gehört, muss die Änderung zunächst auf einen Branch in einem eigenen Fork der Bibliothek gelangen.

Git bietet dafür zwei naheliegende Rezepte: Submodule und Subtrees.

<!-- Erstellt für die ausführbaren Beispiele ein Monorepo sowie lokale Upstream- und Fork-Repositories. -->
<!--
```scrut {fail_fast: true, output_stream: combined}
$ source "$TESTDIR/../scrut-setup.sh"
```
-->

## Rezept 1: Die Bibliothek als Submodul

Ein Submodul lässt die Bibliothek ein eigenes Repository bleiben. Das Monorepo speichert lediglich, welcher Commit davon unter `vendor/library` ausgecheckt sein soll:

```scrut
$ git -c protocol.file.allow=always submodule add -q "$LIBRARY_FORK" vendor/library && \
> git commit -qm "application: add library as a submodule"
```

Der Patch entsteht innerhalb dieses verschachtelten Repositorys. Er wird dort committed und direkt in den Fork des Teams gepusht:

```scrut
$ git -C vendor/library switch -qc feature/custom-patch && \
> printf '%s\n' "export const answer = 43;" >vendor/library/index.js && \
> git -C vendor/library add index.js && \
> git -C vendor/library commit -qm "library: support the application" && \
> git -C vendor/library push -qu origin feature/custom-patch && \
> git ls-remote --exit-code --heads "$LIBRARY_FORK" feature/custom-patch >/dev/null && \
> echo "patch is ready for a pull request"
patch is ready for a pull request
```

Zuletzt muss auch das Monorepo den neuen Submodul-Commit festhalten:

```scrut
$ git add vendor/library && \
> git commit -qm "application: use patched library"
```

Technisch ist das eine saubere Trennung: Der Branch für den Pull Request enthält nur Bibliothekscode und behält dessen ursprüngliche Historie. Im Alltag arbeitet das Team aber ständig mit zwei Repository-Zuständen:

- Ein Clone braucht `--recurse-submodules` oder einen nachträglichen `git submodule update --init --recursive`.
- Das Submodul landet häufig auf einem detached `HEAD`; vor einem Commit muss bewusst ein Branch ausgecheckt werden.
- Ein Anwendungs-Branch besteht aus Commits in zwei Repositories. Sie müssen in der richtigen Reihenfolge gepusht werden, damit der gespeicherte Zeiger erreichbar bleibt.
- Branch-Wechsel, Rebases und Merge-Konflikte können sowohl den Working Tree des Monorepos als auch den des Submoduls betreffen.
- IDEs, Hooks und CI müssen wissen, dass `vendor/library` kein gewöhnlicher Ordner ist.

Submodule modellieren die Repository-Grenze exakt. Gerade deshalb ist sie bei fast jedem Arbeitsschritt sichtbar.

## Rezept 2: Die Bibliothek als Subtree

Ein Subtree macht den umgekehrten Kompromiss. Die Dateien der Bibliothek sind normale Dateien des Monorepos. `git subtree` importiert sie unter einem Präfix; `--squash` fasst ihre bisherige Historie zusammen:

```scrut
$ cd "$EXAMPLE_ROOT/subtree-monorepo" && \
> git remote add library "$LIBRARY_FORK" && \
> git subtree add --prefix=vendor/library --squash library main >/dev/null 2>&1 && \
> test -f vendor/library/index.js && echo "library is part of the working tree"
library is part of the working tree
```

Der Patch ist nun ein gewöhnlicher Monorepo-Commit. `git subtree push` rekonstruiert daraus einen Branch, dessen Wurzel `vendor/library` ist, und pusht ihn in den Fork:

```scrut
$ printf '%s\n' "export const answer = 43;" >vendor/library/index.js && \
> git add vendor/library/index.js && \
> git commit -qm "library: support the application" && \
> git subtree push --prefix=vendor/library library feature/custom-patch >/dev/null 2>&1 && \
> git ls-remote --exit-code --heads "$LIBRARY_FORK" feature/custom-patch >/dev/null && \
> echo "patch is ready for a pull request"
patch is ready for a pull request
```

Das Entwicklererlebnis im Working Tree ist deutlich einfacher: Clone, Branch-Wechsel und Anwendungs-Tests brauchen keine Submodul-Befehle. Dafür bezahlt das Repository an anderer Stelle.

Auch mit `--squash` bleibt die Historie nicht linear. `git subtree add` erzeugt einen Commit mit der zusammengefassten Bibliothekshistorie und mergt ihn in das Monorepo:

```scrut
$ git rev-list --min-parents=2 --count HEAD
1
```

Jeder spätere `git subtree pull --squash` setzt diese Seitenhistorie fort und erzeugt einen weiteren Merge. Christophe Porteneuve zeigt diesen überraschenden Graphen ausführlich in [Mastering Git subtrees](https://medium.com/@porteneuve/mastering-git-subtrees-943d29a798ec).

Auch das Zurückschreiben ist nicht kostenlos. `git subtree split` muss die Monorepo-Historie untersuchen und für die Commits, die den Ordner betreffen, eine neue Historie aufbauen. Das wird in großen, langlebigen Repositories spürbar langsam; wiederholte Pushes bezahlen diese Arbeit erneut.

## Zwei richtige Modelle mit unterschiedlichen Kosten

Beide Rezepte bringen den Patch in einen Fork des Teams, von dem aus ein Pull Request an die Bibliothek möglich ist:

- Submodule bewahren Repository und Historie der Bibliothek, verlagern die Komplexität aber in jeden Checkout und viele alltägliche Git-Befehle.
- Subtrees geben dem Team einen gewöhnlichen Monorepo-Working-Tree, verlagern die Komplexität aber in den Commit-Graphen und die Rekonstruktion der Historie.

Das ist der eigentliche Zielkonflikt: Eine Repository-Grenze soll beim Veröffentlichen erhalten bleiben, ohne die Arbeit innerhalb des Monorepos ständig zu bestimmen. Git liefert beide Bausteine dafür, aber keine der beiden Varianten macht diese Grenze zugleich unsichtbar, linear und günstig.
