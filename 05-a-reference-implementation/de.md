---
title: "Eine Referenzimplementierung"
description: "Es kommt darauf an, wie sich Spleißen in jedem Workflow verhalten soll; die Referenzimplementierung zeigt, dass sich die Spezifikation umsetzen lässt."
topics: [git, testing]
question: "Schreibt ihr auf, wie sich euer Werkzeug verhalten soll, bevor ihr es baut?"
docs: ../git-splice/test/scenarios/README.md
---

git-splice ist ein Werkzeug, aber um das Werkzeug geht es mir nicht. Mir geht es um die Workflows: Wie soll sich Spleißen verhalten, wenn ich auf einem Branch arbeite, wenn ein Pull Request per Squash-Merge gemergt wird oder wenn jemand die Historie des anderen Repos umschreibt?

## Szenarien

Für jede dieser Situationen schreibe ich ein Szenario: ein kleines Beispiel mit einem Zustand vorher, einem Befehl und dem Zustand danach. Darin entscheide ich, wie sich ein Werkzeug verhalten *sollte*. Zusammen sind die Szenarien die Spezifikation:

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

## Wozu dann bauen?

Die Spezifikation hängt nicht an Git. Ein Werkzeug für Sapling oder Jujutsu, das sich so verhält, wie es die Szenarien sagen, würde genauso spleißen.

Dass ich gleichzeitig die Referenzimplementierung schreibe, zeigt, dass sich die Spezifikation umsetzen lässt. Und es hält die Spezifikation ehrlich: Ein Szenario, das kein Werkzeug erfüllen kann, fällt sofort auf.

Wie sich ein Szenario selbst prüft, zeige ich in der nächsten Folge.
