---
title: "Lessons Learned"
description: "Die Dateien des anderen Repos in einen Ordner kopieren, den zuletzt synchronisierten Commit merken, und dieser Commit ist die Basis eines Three-Way-Merges."
topics: [git]
question: "Was bräuchtet ihr noch, um zwei Repositories dauerhaft zu synchronisieren?"
docs: ../git-splice/test/concepts/splice-file/README.md
---

Weder Git-Submodule noch `git subtree` sind eine gute Lösung, um zwei Repositories kontinuierlich miteinander zu synchronisieren.

Um das Beste aus beiden Welten zu kombinieren, brauchen wir getrennte Historien, wie bei Submodulen. Gleichzeitig soll das Monorepo die Dateien des Sub-Repos enthalten, wie bei `git subtree`. Dadurch funktionieren die Standardbefehle wie `git status` und `git log` weiterhin so, wie man es gewohnt ist.

## Nur die Dateien

Das ist doch nicht so schwierig: Wir kopieren die Dateien des anderen Repos in einen Ordner des Monorepos, und fertig:

```text
a.git                         monorepo/
                              ├── app/
                              │   └── main.js
                              └── vendor/
.  ──────── copy ──────────►      └── a/
├── src/                              ├── src/
│   └── parse.js                      │   └── parse.js
└── README.md                         └── README.md
```

Es werden keine Commits ausgetauscht. Das Monorepo bekommt nicht die Historie des anderen Repos, und das andere Repo nicht die des Monorepos. Ein Fix in `vendor/a/` und der Code in `app/`, der ihn aufruft, sind ein ganz normaler Commit.

## Ein Synchronisationspunkt

Wir merken uns nur eines: welchen Commit des anderen Repos wir zuletzt kopiert haben. Er ähnelt einem Gitlink, verspricht aber nicht, dass es sich um den ausgecheckten Commit handelt. Es reicht, wenn es der zuletzt *synchronisierte* Commit ist. Eine kleine Datei im Ordner hält ihn fest, zusammen mit der URL, die wir aus `.gitmodules` kennen:

```text
[splice]
	commit = 3f1c…
[upstream "origin"]
	url = git@github.com:x/a.git
```

Die Datei ist eingecheckt. So zieht sie immer mit dem Ordner mit, und Rewrites der Commits können sie nicht verlieren.

## Ein Three-Way-Merge

In der Zwischenzeit entwickeln sich beide Seiten weiter. Um sie zusammenzubringen, reicht ein ganz normaler Three-Way-Merge:

```text
BASE     vendor/a/, wie wir ihn zuletzt kopiert haben, bei 3f1c…
OURS     vendor/a/ im Monorepo, wie er jetzt ist
THEIRS   a.git, wie es jetzt ist
```

Der Synchronisationspunkt ist die Basis. Git vergleicht unsere und ihre Dateien mit ihr und übernimmt die Änderungen beider Seiten. Wir müssen nicht zwei Historien in Einklang bringen wie bei `git subtree`, es geht nur um Dateiänderungen.

Synchronisieren verschiedene Branches zu verschiedenen Zeiten, kann es am Synchronisationspunkt zu Konflikten kommen. Das ist aber gewünscht, und wir lösen sie so, wie wir es von Git gewohnt sind.
