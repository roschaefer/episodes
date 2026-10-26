# Why "splice"

![Rope splices from the Nordisk familjebok, a long splice on the left](../images/rope-splices-nordisk-familjebok.png)

*Rope splices, a) a long splice, from the Nordisk familjebok, 2nd edition,
vol. 26 (1917). Public domain, via
[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Splitsar.png).*

A [splice](https://en.wikipedia.org/wiki/Splice) joins two things into
one: ropes, film, tape, wires, optical fibres, wooden beams, genes. The
name `git-splice` borrows from all of them.

## A concept, and its reference implementation

Splicing is a concept: copy another repository's files into a folder,
keep the last synced commit, and bring both sides together with a
three-way merge. The [scenarios](../../test/scenarios/README.md) specify
how splicing behaves, one situation at a time. `git-splice` is its
reference implementation, for Git: it shows that the specification can
be built. A tool for another version control system could splice too,
and the name belongs to the concept, not to the tool.

## Rope splicing

A [long splice](https://en.wikipedia.org/wiki/Rope_splicing) unlays the
strands of two ropes and weaves each into the other. Unlike a knot, or
even a short splice, it adds no lump: the joint has nearly the rope's own
diameter and runs through a pulley like the rest of the rope.

`git-splice` works the same way. The upstream's files are woven into the
monorepo as an ordinary folder, with no submodule pointer (gitlink) and
nothing extra to check out. You see the joint only as one small file,
`<path>/.splice`, which records the upstream.

## Noun and verb

As a noun, a splice is the joint: here, the folder together with its
connection to the upstream repository. "The `vendor/a/` splice" is the
folder `vendor/a/` and the upstream it syncs with.

As a verb, you splice something in or out:

- **splice in**: bring upstream content into the monorepo, with `clone`,
  `merge` and `pull`.
- **splice out**: publish the monorepo's changes upstream, with `push`.

The [vocabulary](README.md#vocabulary) defines these and the
other terms.

## Words of the version control system, and new words

The names of splicing follow one rule:

- A word the version control system already uses, like Git's `status`,
  `pull`, `upstream` or `rebase`, does what it does there.
- A new word must not collide with one it already uses.

"Splice" is a new word: Git doesn't use it, so it doesn't collide, but it
has to be coined. An everyday word would be easier to pick up, but most
of them are taken.

## RNA splicing

In [RNA splicing](https://en.wikipedia.org/wiki/RNA_splicing), a cell cuts
the introns out of a gene's transcript and joins the remaining exons into
one continuous strand.

`push` does something similar to the monorepo's history. A monorepo commit
may touch the splice and `app/` at once. The rebuild keeps only the part
inside the folder, drops commits that don't touch it, and joins the rest
into a history the upstream can take as its own.

## `Array.prototype.splice`

JavaScript's
[`splice`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/splice)
removes and inserts elements in place: unlike `slice`, it changes the
array it is called on.

```js
const files = ["app", "lib", "docs"];
files.splice(1, 1, "lib v2");  // files is now ["app", "lib v2", "docs"]
```

`git-splice` changes the repository it runs in, too. `pull` merges the
upstream's changes into the folder in place, as an ordinary commit on
your branch, rather than checking them out somewhere else.
