---
title: "Spleißen"
description: "Das Konzept bekommt einen Namen: Ein Spleiß ist ein Ordner samt seiner Verbindung zu einem anderen Repository, und git-splice ist seine Referenzimplementierung."
topics: [git]
question: "Fällt euch ein besserer Name ein? Am liebsten ein alltägliches Wort, das noch keine Versionsverwaltung verwendet."
docs: ../git-splice/docs/design/name.md
---

In der letzten Folge haben wir drei Dinge zusammengesetzt: Wir kopieren die Dateien des anderen Repos in einen Ordner, merken uns den zuletzt synchronisierten Commit und bringen beide Seiten mit einem Three-Way-Merge zusammen. Dieses Konzept braucht einen Namen. Ich nenne es Spleißen.

Ein Spleiß verbindet zwei Dinge zu einem: zwei Seile, zwei Filmstücke, zwei Kabel. Beim Langspleiß werden die Litzen zweier Seile ineinander verflochten. Anders als ein Knoten hinterlässt er keine Verdickung, und das Seil läuft weiter durch eine Rolle:

![Seilspleiße aus dem Nordisk familjebok, links ein Langspleiß](../git-splice/docs/images/rope-splices-nordisk-familjebok.png)

Genau das machen wir mit einem anderen Repository. Seine Dateien werden als ganz normaler Ordner in das Monorepo eingeflochten, ohne Gitlink und ohne etwas zusätzlich auszuchecken. Von der Verbindungsstelle sieht man nur eine kleine Datei in diesem Ordner.

## Substantiv und Verb

Das Wort funktioniert als Substantiv und als Verb:

```text
der Spleiß     der Ordner, samt seiner Verbindung
               zum anderen Repository
einspleißen    die Änderungen des anderen Repos
               in den Ordner holen
ausspleißen    die Änderungen des Ordners zurück
               ins andere Repository schicken
```

## Ein Name für ein Konzept

Spleißen ist ein Konzept, kein Werkzeug. git-splice ist seine Referenzimplementierung, für Git. Auch andere Versionsverwaltungen könnten spleißen.

Deshalb darf der Name nicht mit den Begriffen der Versionsverwaltung kollidieren, in die man ihn einbaut. Begriffe wie `pull`, `upstream` oder `rebase` behalten die Bedeutung, die sie dort haben. Ein neuer Begriff wie „Spleiß“ muss erst geprägt werden: Kaum jemand weiß bisher, was ein Spleiß in einer Versionsverwaltung ist. Alltägliche Wörter wären leichter, aber die meisten sind schon belegt.
