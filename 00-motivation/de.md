---
title: "Motivation"
description: "Manchmal muss ein Ordner in einem Monorepo zugleich ein eigenes Repository sein: ein öffentliches Projekt in einem privaten Monorepo, eine vendorte Bibliothek, Teams mit eigener CI."
topics: [git]
question: "Hattet ihr schon mal eine ähnliche Situation? Musstet ihr euch zwischen einem Monorepo und getrennten Repositories entscheiden?"
---

Ich liebe Monorepos. Mein ganzer Code liegt an einem Ort, ein Commit kann mehrere Projekte auf einmal ändern, und ich teste sie alle zusammen.

```text
monorepo/
├── accounting/
├── app/
├── tools/
└── website/
```

Wenn ein Monorepo möglich ist, ist es fast immer die beste Wahl. Es hält die Komplexität gering, und viele Probleme verschwinden von selbst. Mehrere Projekte leben problemlos im selben Repository, und alle Teams haben Zugriff auf alle Projekte. Aber es gibt Situationen, in denen das leider nicht geht.

## Ein öffentlicher Ordner in einem privaten Monorepo

```text
monorepo/                privat
├── accounting/
└── tools/        <-->   tools.git, öffentlich
```

Ich mache zum Beispiel "Plain Text Accounting": Meine Buchhaltung liegt im selben Repository wie ihre Auswertung. Jetzt möchte ich den Quellcode von meinen Auswertungen als Open-Source-Werkzeuge veröffentlichen. Natürlich nicht das ganze Monorepo, nur die Ordner mit öffentlichem Quellcode.

Den Quellcode einmalig auf GitHub zu veröffentlichen, reicht nicht. Leute eröffnen Issues und Pull Requests, ein Bot aktualisiert die Abhängigkeiten. Diese Commits müssen zurück ins Monorepo, wo ich weiter an den Werkzeugen arbeite, neben allem anderen.

## Eine Bibliothek vendoren

```text
monorepo/
├── app/
└── vendor/lib/   --->   lib-fork.git   --->   lib.git
                                    Pull Request
```

Andersherum: Meine App nutzt eine Bibliothek, die jemand anderes pflegt. Ich finde einen Fehler darin und will ihn beheben. Also kopiere ich den Quellcode der Bibliothek in mein Monorepo, behebe den Fehler dort und teste den Bugfix zusammen mit meiner App.

Dann soll der Bugfix upstream. Das Repository der Bibliothek gehört mir nicht, also muss der Bugfix zuerst auf einen Branch in meinem Fork, als Commit der Bibliothek ohne den Code meiner App. Von dort kann ich einen Pull Request eröffnen.

## Getrennte CI-Pipelines

```text
company/
├── team-a/       <-->   team-a.git, eigene CI
├── team-b/       <-->   team-b.git, eigene CI
└── team-c/       <-->   team-c.git, eigene CI
```

Einige Freunde von mir arbeiten in großen Unternehmen mit vielen Teams. Sie wollen nicht in einem Monorepo arbeiten, weil sie getrennte CI-Pipelines haben wollen. Würde das ganze Unternehmen in einem Monorepo arbeiten, gäbe das ein ziemliches Durcheinander, und die Teams würden sich in der CI gegenseitig blockieren.

## Dreimal dasselbe Problem

```text
monorepo/
└── project/      <-->   project.git
```

In allen drei Fällen hätte ich am liebsten das Beste aus beiden Welten: Ich kann im Monorepo arbeiten oder im Repository des einzelnen Projekts, und die Änderungen fließen in beide Richtungen.
