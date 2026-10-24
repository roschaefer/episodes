---
slug: getrennte-historien-gemeinsame-dateien
title: "Getrennte Historien, gemeinsame Dateien"
description: "Getrennte Historien wie bei Submodulen, die Dateien im Monorepo wie bei git subtree, und dazwischen ein eingecheckter Synchronisationspunkt."
series: why-splicing
seriesOrder: 4
topics: [git]
question: "Was bräuchtet ihr noch, um zwei Repositories dauerhaft zu synchronisieren?"
docs: ../git-splice/test/concepts/splice-file/README.md
---

Weder Git-Submodule noch `git subtree` sind eine gute Lösung, um zwei Repositories kontinuierlich miteinander zu synchronisieren.

Um das Beste aus beiden Welten zu kombinieren, brauchen wir getrennte Historien, wie bei Submodulen. Gleichzeitig soll das Monorepo die Dateien des Sub-Repos enthalten, wie bei `git subtree`. Dadurch funktionieren die Standardbefehle wie `git status` und `git log` weiterhin so, wie man es gewohnt ist.

So kommt alles zusammen, was zusammengehört, anders als bei Submodulen: Ein Fix im Sub-Repo und der Code, der ihn aufruft, sind ein Commit.

## Ein Synchronisationspunkt

Damit das Neuberechnen der Commits skaliert, brauchen wir einen Synchronisationspunkt. Er ähnelt einem Gitlink, verspricht aber nicht, dass es sich um den ausgecheckten Commit handelt. Es reicht, wenn es der zuletzt *synchronisierte* Commit ist.

In derselben Datei können wir auch die Konfiguration ablegen, die wir aus `.gitmodules` kennen, etwa die URL:

```text
[splice]
	commit = 3f1c…
[upstream "origin"]
	url = git@github.com:x/a.git
```

Die Datei liegt im Ordner des Sub-Repos. So zieht sie immer mit dem Ordner mit. Und weil sie im Worktree eingecheckt ist, hat jeder Worktree seine eigene: Veränderliche Zustände sind voneinander getrennt, statt wie bei Submodulen geteilt in der `.git/config`. Sie kann auch nicht durch Rewrites der Commits verloren gehen, anders als die Sync-Punkte von `git subtree` in den Commit-Nachrichten.

## Ein Three-Way-Merge

Um die geänderten Dateien abzugleichen, reicht ein ganz normaler Three-Way-Merge. Wir müssen nicht zwei Historien in Einklang bringen wie bei `git subtree`, es geht nur um Dateiänderungen.

Synchronisieren verschiedene Branches zu verschiedenen Zeiten, kann es in dieser Datei zu Konflikten kommen. Das ist aber gewünscht, und wir lösen sie so, wie wir es von Git gewohnt sind.
