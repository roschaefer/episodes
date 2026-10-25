---
title: "Motivation"
description: "Sometimes a folder in a monorepo has to be a repository of its own as well: a public project in a private monorepo, a vendored library, teams with their own CI."
topics: [git]
question: "Have you ever been in a similar situation? Have you had to decide between a monorepo and separate repos?"
---

I love monorepos. All my code is in one place, one commit can change several projects at once, and I test them all together.

```text
monorepo/
├── accounting/
├── app/
├── tools/
└── website/
```

If a monorepo is possible, it is almost always the best choice. It keeps complexity low, and many problems go away by themselves. Several projects live side by side in the same repository, and every team has access to every project. But there are situations where, unfortunately, that doesn't work.

## A public folder in a private monorepo

```text
monorepo/                private
├── accounting/
└── tools/        <-->   tools.git, public
```

For example, I do "plain text accounting": my bookkeeping lives in the same repository as its reports. Now I want to publish the source code behind those reports as open source tools. Of course not the whole monorepo, only the folders with public source code.

Publishing the source code on GitHub once isn't enough. People open issues and pull requests, a bot updates the dependencies. Those commits have to come back into the monorepo, where I keep working on the tools next to everything else.

## Vendoring a library

```text
monorepo/
├── app/
└── vendor/lib/   --->   lib-fork.git   --->   lib.git
                                    pull request
```

The other way round: my app uses a library that someone else maintains. I find a bug in it and want to fix it. So I copy the library's source into my monorepo, fix the bug there and test the bugfix together with my app.

Then the bugfix should go upstream. I don't own the library's repository, so the bugfix first has to reach a branch in my fork, as a library commit without any of my app's code. From there I can open a pull request.

## Separate CI pipelines

```text
company/
├── team-a/       <-->   team-a.git, own CI
├── team-b/       <-->   team-b.git, own CI
└── team-c/       <-->   team-c.git, own CI
```

Some friends of mine work at large companies with many teams. They don't want to work in one monorepo, because they want separate CI pipelines. If the whole company worked in one monorepo, it would get quite messy, and the teams would block each other in CI.

## The same problem three times

```text
monorepo/
└── project/      <-->   project.git
```

In all three cases I'd like the best of both worlds: I can work in the monorepo or in the project's own repository, and the changes flow both ways.
