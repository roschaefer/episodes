---
title: "Specification by Example"
description: "Es kommt darauf an, wie sich Spleißen in jedem Workflow verhalten soll; Szenarien spezifizieren es an Beispielen, und Scrut und eine Prüfung der Zeichnungen halten die Beispiele wahr."
topics: [git, testing]
question: "Schreibt ihr auf, wie sich euer Werkzeug verhalten soll, bevor ihr es baut?"
docs: ../git-splice/test/scenarios/README.md
---

git-splice ist ein Werkzeug, aber um das Werkzeug geht es mir nicht. Mir geht es um die Workflows: Wie soll sich Spleißen verhalten, wenn ich auf einem Branch arbeite, wenn ein Pull Request per Squash-Merge gemergt wird oder wenn jemand die Historie des anderen Repos umschreibt?

## Szenarien

Für jede dieser Situationen schreibe ich ein Szenario: ein kleines Beispiel mit einem Zustand vorher, einem Befehl und dem Zustand danach. Das ist Specification by Example: Nicht „status zeigt, wie weit der Spleiß voraus ist“, sondern: Dieser Befehl gibt in dieser Situation genau das aus. Zusammen sind die Szenarien die Spezifikation:

```text
test/scenarios/
├── 01-everyday-sync/
├── 02-starting-a-splice/
├── 03-branches-and-teamwork/
├── 04-upstreams/
├── 05-nested-splices/
├── 06-rewritten-history/
└── 07-moved-folders/
```

Ihr könnt sie alle hier nachlesen:

```text
https://roschaefer.github.io/git-splice/test/scenarios/
```

## Beispiele, die laufen

Jedes Szenario ist eine Markdown-Datei, und ihre Beispiele laufen. Dafür nutze ich Scrut, ein Werkzeug von Meta. In einem Codeblock, der mit `scrut` markiert ist, steht ein Befehl nach dem `$`, und darunter die Ausgabe, die ich erwarte:

```console
$ git splice status
On branch main

  ahead 2, behind 3  lib
```

Scrut führt den Befehl aus und vergleicht. Gibt git-splice etwas anderes aus, schlägt der Test fehl.

## Zeichnungen, die geprüft werden

Die Szenarien zeichnen auch die Commit-Graphen. Eine Zeichnung veraltet, ohne dass es jemand merkt. Deshalb liest eine Prüfung sie, schlägt jeden Commit und jeden Pfeil in den echten Repositories nach und nennt jeden Unterschied:

```console
$ check_drawing <drawing>
!!   R points at d', the code says e'
!!   b' is solid, but no upstream branch has it: dash it
```

Text, Ausgabe und Zeichnungen sind zusammen die Akzeptanztests. Spleißen funktioniert, wenn sie durchlaufen.

## Wozu dann bauen?

Die Spezifikation hängt nicht an Git. Ein Werkzeug für Sapling oder Jujutsu, das sich so verhält, wie es die Szenarien sagen, würde genauso spleißen.

Dass ich gleichzeitig die Referenzimplementierung schreibe, zeigt, dass sich die Spezifikation umsetzen lässt. Und es hält die Spezifikation ehrlich: Ein Szenario, das kein Werkzeug erfüllen kann, fällt sofort auf.
