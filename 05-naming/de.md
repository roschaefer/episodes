---
title: "Warum es git-splice heißt"
description: "Was ein Splice ist, und die Regel für die Begriffe von git-splice: Begriffe aus Git tun, was sie in Git tun, neue Begriffe kollidieren nicht mit ihnen."
series: git-splice
seriesOrder: 1
topics: [git]
question: "Fällt euch ein besserer Name ein? Am liebsten ein alltägliches Wort, das in Git noch nicht belegt ist."
docs: ../git-splice/docs/design/name.md
---

Ein Splice verbindet zwei Dinge zu einem: zwei Seile, zwei Filmstücke, zwei Kabel. Beim langen Spleiß werden die Litzen zweier Seile ineinander verflochten. Anders als ein Knoten hinterlässt er keine Verdickung, und das Seil läuft weiter durch eine Rolle.

git-splice macht dasselbe mit einem anderen Repository. Seine Dateien werden als ganz normaler Ordner in das Monorepo eingeflochten, ohne Gitlink und ohne etwas zusätzlich auszuchecken. Von der Verbindungsstelle sieht man nur eine kleine Datei in diesem Ordner, `.splice`.

## Eine Regel für Namen

Wenn ich in git-splice etwas benenne, folge ich einer Regel mit zwei Teilen:

1. Begriffe aus Git, wie `status`, `pull`, `upstream` oder `rebase`, tun in git-splice das, was sie in Git tun.
2. Neue Begriffe dürfen nicht mit denen kollidieren, die Git schon verwendet.

„Splice“ ist so ein neuer Begriff. Git verwendet ihn nicht, also kollidiert er nicht. Aber weil er neu ist, muss ich ihn erst prägen: Noch weiß niemand, was ein Splice in Git ist.

Deshalb suche ich noch. „Splice“ funktioniert bisher, aber ich hätte nichts gegen ein alltägliches Wort, das in Git noch nicht belegt ist.
