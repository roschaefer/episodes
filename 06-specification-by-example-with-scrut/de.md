---
title: "Specification by Example mit Scrut"
description: "Die Dokumentation von git-splice ist ihre Testsuite: Scrut führt die Befehle im Markdown aus und vergleicht ihre Ausgabe."
topics: [git, testing]
question: "Wer schreibt und wer prüft bei euch im Team die Akzeptanztests?"
docs: ../git-splice/README.md
---

Die Dokumentation von git-splice ist gleichzeitig seine Testsuite. Dafür nutze ich Scrut, ein Werkzeug von Meta. In einer Markdown-Datei steht in einem Codeblock, der mit `scrut` markiert ist, ein Befehl nach dem `$`, und darunter die Ausgabe, die ich erwarte:

```console
$ git splice status
On branch main

  ahead 2, behind 3  lib
```

Scrut führt den Befehl aus und vergleicht. Gibt git-splice etwas anderes aus, schlägt der Test fehl. Die README, die ihr lest, ist also dieselbe Datei, die die CI ausführt, und sie kann nicht hinter dem Werkzeug zurückbleiben.

## Drei Begriffe

Ein **Test** prüft, ob Code tut, was er soll. Meistens ist er in Code geschrieben, für Entwickler.

**Specification by Example** geht einen Schritt weiter: Die Anforderung selbst wird als konkrete Beispiele aufgeschrieben. Nicht „status zeigt, wie weit der Splice voraus ist“, sondern: Dieser Befehl gibt in dieser Situation genau das aus.

**Acceptance Test-Driven Development** schreibt diese Beispiele vor dem Code. Sie sind die Akzeptanztests: Das Feature ist fertig, wenn sie durchlaufen.

## Die Rollen tauschen

Im klassischen ATDD hat der Product Owner die Akzeptanztests geprüft, und der Entwickler hat sie umgesetzt.

Mit KI-Agenten tauschen sich die Rollen. Ich prüfe die Akzeptanztests, und der Agent setzt sie um.

Für mich ist das ein guter Weg, mit KI zu arbeiten.
