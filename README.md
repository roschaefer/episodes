# Episodes

Each numbered folder here is one episode of a series about splicing, and
the single source for both its blog post on [roschaefer.de](https://roschaefer.de)
and its video on PeerTube. The post stands on its
own, with text and diagrams; it may link to the video, but embeds nothing.
Each language has its own post and its own video, which I speak myself.

```
episodes/<nn>-<id>/en.md   the English post, and the script for the English video
episodes/<nn>-<id>/de.md   the German post, and the script for the German video
episodes/<nn>-<id>/*.svg   diagrams that belong to this episode only
episodes/series.toml       the series the episodes make: its title and description
episodes/git-splice/       git-splice, spliced in: the docs and diagrams the episodes cite
```

`<nn>` is the episode's place in the series, as in the playlist: the
build writes it into the post as `seriesOrder`. To reorder, rename the
folders. `<id>` is the post's `id`, the same in both languages.

The frontmatter is the blog's (see
`roschaefer.de/src/lib/blog/posts.ts`), without `id`, `series` and
`seriesOrder`, which the build adds from the folder name and
`series.toml`, plus optionally `docs`, the chapter of the git-splice
docs the episode goes with, e.g. `../git-splice/test/comparisons/git-subtree.md`.
The post and the video end with a link to it.

The title is neutral: it names the subject and doesn't judge it, e.g.
"Git Submodules", not "What goes wrong with Git submodules". It is the
same everywhere: the post's title, the video's on the platform, and the
title card the video opens with. The post's slug, its file name and
URL, is the title written for a URL ("Warum es git-splice heißt" becomes
`warum-es-git-splice-heisst`). A published episode pins it with `slug`,
so that retitling it keeps its URL; the build refuses one without.

Every episode then ends with `question`, a question that asks the viewer
for technical feedback, e.g. "Have you ever used Git submodules, and what
was your developer experience?" The post and the video add "Write it in
the comments below." The build refuses to publish an episode without one.

The thorough documentation lives in git-splice, in texts and diagrams
its tests check. An episode is a short, easy summary of the essentials,
and points to its chapter for the rest: episode 01 shows the two places
of a submodule a user sees, and only says that there are four more.

An episode and its chapter grow together: when explaining something
shows that the chapter is unclear or missing a step, fix the chapter in
`git-splice/` in the same commit, then `git splice push git-splice`.
`just check` runs the git-splice docs' tests along with the episodes'.

An episode that runs a chapter's commands tells viewers how to run them
too: `just sandbox <page>`, in a clone of git-splice, opens a shell in
the state the page starts from (see `git-splice/docs/sandbox.md`). The
first such episode, 01, explains it.

Images use paths relative to the file, so they render in any Markdown
preview. Diagrams the git-splice docs already test are referenced where
they live, e.g. `../git-splice/test/comparisons/git-subtree-rejoin.drawio.svg`,
so the post shows what the tests check.

## Branches

`main` is what's published: this folder without the numbered episodes,
until one is. `development` holds every episode, published or not, and
is where they're written. Tooling, like `video/` or this README, changes
on `main`, and `main` is merged into `development`.

To have one or more episodes reviewed, cut a branch from `main`, bring
only those episodes over from `development`, and open a draft pull
request to `main`. The review bots then look at nothing else:

```sh
git switch -c review/submodules main
git restore --source development -- episodes/01-submodule-problems
git commit -m "docs(episodes): add Git Submodules"
git splice push episodes   # creates the branch upstream
gh pr create --draft --repo roschaefer/episodes --base main --head review/submodules
```

Once the pull request is squash-merged, `git splice pull episodes` on
`main` brings it back, and `main` is merged into `development`.

## Building the blog posts

Each `<lang>.md` becomes a post: `video/blog.py` writes it, with the
frontmatter the website reads and the same ending as the video, into a
website's folders, copies the images it shows, and writes the series
as JSON. Which folders those are is
the website's business: my monorepo has this folder and roschaefer.de
spliced in side by side and passes roschaefer.de's, which is deployed
from its own repository:

```sh
just episodes        # in the monorepo: writes src/content/blog/<lang>/<slug>.svx, static/blog/episodes/ and src/lib/blog/series.json
just episodes-check  # fails if those are out of date
```

Edit the episode here, not the generated `.svx`: the next build overwrites
it. `static/blog/episodes/` belongs to the build, which removes images no
episode references any more.

## Building the video

Each video comes from the post in its language, `en.md` or `de.md`, with
Manim and manim-voiceover (`video/episode.py`). Each heading, diagram, or
code block becomes a block of the video, and the prose after it, up to
the next block, is what I say over it, one voiceover per paragraph. A
paragraph that ends in a colon introduces the next block, so it plays
over that one: "This command writes to six places:" shows the command
while I say it. The prose before the first block plays over a title card. The two videos
don't share timing: each block lasts as long as I take to say it in that
language, so they are two files, not one with two audio tracks.

The recipes run in this folder (from the monorepo: `just episodes/video <id>`):

```sh
just video <id>              # or its number; English preview, with a computer voice (Piper)
just video <id> de           # the German preview
just video <id> de h         # the same in full HD
just video <id> en l silence # silence as long as reading the text takes
just record <id> de          # record each German paragraph not recorded yet, then render
just slides <id> de          # the German slides, a PDF with one page per block
just video-test              # test how an episode becomes blocks and a post
```

Recordings land in `<nn>-<id>/voiceovers/<lang>/`, named by their text, and
belong in Git. Change a paragraph and only that one needs recording again.
The video and its subtitles (`.srt`) are written to
`media/videos/episode/<quality>/` as `<nn>-<id>-<lang>.mp4`; a preview adds
`-piper` or `-silence`.

The slides for a talk are the video's blocks as stills, as the video shows
them: `just slides <id> <lang>` writes `media/slides/<nn>-<id>-<lang>.pdf`,
at 13.33 by 7.5 inches, the size of a widescreen slide.

To record, `just record <id> <lang>` shows
each paragraph not recorded yet: press Enter, wait a second, speak, and
press Enter again. Then `l` listens to the take, `r` records it again and
`a` accepts it. Ctrl-C keeps the takes accepted so far, and the next run
goes on from there. It records from the default microphone and plays
through the default speakers, as PipeWire has them, and says which
microphone it records from (`wpctl status` lists them, `wpctl set-default
<id>` picks one).

```sh
just voiceovers <id> <lang>              # the paragraphs, numbered, and which are recorded
just retake <id> <lang> <paragraph>...   # discard bad takes; just record asks again
just voiceovers-prune <id>               # discard takes of text the scripts no longer have
```

`just check` fails while an episode has takes of text it no longer has.

The text is written for readers, and I speak it in my own words: what
reads best isn't always what I'd say. A numbered list reads better than
"First, … Second, …", and "in der CI" is correct where I'd say "auf CI".
So the post says "1." and "in der CI", and the recording says "Erstens"
and "auf CI". The subtitles show the text, not the recording.

Commands and URLs are shown, not said. A command goes in a code block;
the prose says what it is. In prose, a link's text is read out, never
its URL. The closing slide shows the docs chapter's address, with its QR
code. A code block's `#` line above the commands adds another address
for the video, where its prose links can't be clicked: only for a page
the closing slide doesn't link, e.g. episode 01's sandbox. The video
shows it small, by its QR code, not as code; the post leaves it out, as
its prose links there anyway.

Code blocks are shown, not run. scrut checks that they behave as shown,
in the git-splice docs they come from.

Diagrams from draw.io work, but `video/episode.py` has to strip their CSS
and turn their text into paths with Inkscape first.

The recipes run in the dev shell, `nix develop`, which has
everything uv doesn't install: ffmpeg, Inkscape, SoX, the diagrams' font,
Piper's English and German voices, and the libraries the Python packages
build against.
