# Personal website

Site generated with [Zola](https://www.getzola.org/). Blog posts rendered from [Quarto](https://quarto.org/) source.

[![Netlify Status](https://api.netlify.com/api/v1/badges/fbc483b6-8147-45ad-9e78-f11e6e5d1e53/deploy-status)](https://app.netlify.com/sites/mikedecr/deploys)


## Setup

Requires [pixi](https://pixi.sh/latest/).

```sh
git clone git@github.com:mikedecr/website.git && cd website
git submodule update --init --recursive
pixi install
pixi run zola --root zola serve --drafts
pixi run zola --root zola build
```
