# AGENTS.md

Personal website [mikedecr.computer](https://mikedecr.computer).
README.md for setup.

Managed by a pixi env.
Pixi tasks control build.

- link: hardlinks blog posts into `zola/content/`
- build / serve: self-explanatory

Blog posts are brought in with a submodule.
Some posts are their own nested submodules when they are complex.
Blog posts should provide their own .md artifact and accompanying files (the site doesn't concern itself with rendering).
`mkd.toml` defines how to link files from submodule into site content directory.


## Architecture

- **`src/mkd/`** — Python CLI (`python -m mkd link`).
Reads `mkd.toml` `[links]` section and hardlinks `.md` files from submodule blog dirs into `zola/content/`.
- **`mkd.toml`** — Link config: `dest = "source"` pairs under `[links]`.
- **`zola/`** — Zola site (deployed). Config: `zola/config.toml`, deploy: `zola/netlify.toml`.
