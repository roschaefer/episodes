---
title: "Git-Remotes sind die falsche Grenze für einen Ordner"
description: "Ein Remote repräsentiert immer ein Repository. Es nach einem Monorepo-Ordner zu benennen ließ einen katastrophalen Push normal aussehen – und offenbarte einen Designfehler in git-subtrees."
topics: [git]
docs: ../git-splice/docs/design/accidental-monorepo-push.md
---

Die ursprüngliche Konfiguration von `git-subtrees` hatte eine reizvolle Regel: Der Name des Remotes war gleichzeitig der Pfad des Ordners.

```text
vendor/parser  →  Remote "vendor/parser"
libs/model     →  Remote "libs/model"
```

Eine eigene Konfigurationsdatei war unnötig. Git kannte bereits die URLs, und Remote-Tracking-Refs hielten die Upstream-Branches. Die Regel suggerierte jedoch etwas, das Git nicht durchsetzen konnte: Ein Remote namens `vendor/parser` repräsentiere nur `vendor/parser/`.

Das tat es nie. Ein Git-Remote repräsentiert ein **ganzes Repository**.

## Der gefährliche Befehl sieht richtig aus

Die sichere Operation extrahiert zuerst den Ordner und pusht den rekonstruierten Commit:

```sh
git subtree push --prefix=vendor/parser vendor/parser main
```

Ein ausgelassenes Wort ändert die Bedeutung vollständig:

```sh
git push vendor/parser main
```

Nun sendet Git den `main`-Branch des Monorepos samt aller anderen Ordner und ihrer Historie an das Parser-Repository. Der Remote-Name lässt den Befehl begrenzt aussehen. Für Git existiert diese Grenze nicht.

[Issue #50](https://github.com/roschaefer/git-subtrees/issues/50) dokumentiert weniger offensichtliche Wege zum gleichen Ergebnis. `push.autoSetupRemote` kann das einzige konfigurierte Remote auswählen. Der Sync-Button einer IDE folgt einem versehentlich gesetzten Upstream. LazyGit schlägt ohne `origin` möglicherweise das erste Remote vor. Dazu kommen `git push --all`, `--mirror`, die Shell-Historie und Force-Pushes.

Den Branch danach zu löschen macht die Daten nicht wieder privat. Wer sie gefetcht oder geforkt hat, besitzt eine Kopie; Hosting-Anbieter können weiterhin über ihre SHA erreichbare Objekte behalten.

## Meine erste Reaktion behandelte es als Bedienfehler

Die unmittelbare Lösung war ein `pre-push`-Hook. Er untersuchte ausgehende Commits und verweigerte einen Monorepo-förmigen Baum für ein Subtree-Remote.

Diese Leitplanke half, aber ihre Grenzen waren aufschlussreich:

- Hooks werden nicht geklont.
- `--no-verify` umgeht sie.
- Hook-Manager konkurrieren um denselben Einstiegspunkt.
- Jeder Clone muss den Schutz korrekt installieren.
- Jeder neue Push-Weg muss weiterhin erkannt werden.

Ich untersuchte außerdem gesperrte Push-URLs und ein eigenes Remote-Protokoll. Jede Variante baute zusätzliche Mechanik um eine Fähigkeit, die Nutzer gar nicht brauchten.

## Die Fähigkeit entfernen

Zum Fetchen braucht es kein konfiguriertes Remote. Git kann eine URL direkt in einen privaten Namensraum fetchen:

```sh
git fetch <url> '+refs/heads/*:refs/splices/<path>/*'
```

Auch ein Push braucht kein Remote. Git Splice kann die Historie des Ordners rekonstruieren und genau diesen Commit mit URL und Refspec senden.

Die URL gehört in die eingecheckte Zustandsdatei des Ordners. Private Refs halten die gefetchten Branches für Vergleiche und Merges. Es gibt kein benanntes Remote mehr, das ein gewöhnliches `git push` versehentlich treffen könnte.

Das beseitigt mehr als ein Sicherheitsrisiko. Remote-Namen können nicht kollidieren. Ein verschobener Ordner erfordert kein Umbenennen. Autovervollständigungen schlagen Upstream-Repositories nicht mehr als Push-Ziele vor. Neue Clones kennen die Zuordnung sofort, weil sie mit dem Working Tree reist.

Remotes hatten den ersten Entwurf angenehm klein gemacht. Doch knappe Konfiguration ist nicht automatisch ein korrektes Modell. Die Beziehung zwischen Ordner und Repository braucht eine URL und Refs. Sie muss nicht so tun, als sei der Ordner selbst ein lokales Repository.

Die sicherste ungültige Operation ist nicht die, die ein kluger Hook abfängt. Es ist die, die der Entwurf gar nicht ausdrücken kann.
