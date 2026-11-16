# Contributing

## Commits

Commits follow [Conventional Commits](https://www.conventionalcommits.org): `type(scope): Description`, with the description in imperative and starting with a capital letter.

```
feat(assets): Add Tom Belsø and Felipe Drugovich
fix(assets): Replace the photo of Alain Prost
feat(scripts): Download several images at the same time
docs: Explain how to add a photo by hand
```

### Types

| Type | Use it for |
|---|---|
| `feat` | A new image, or a new feature of the scripts |
| `fix` | Replacing an image that was wrong, or fixing a bug of the scripts |
| `perf` | Making the scripts faster |
| `refactor` | Changing the scripts without changing what they do |
| `docs` | README and other documentation |
| `test` | Tests |
| `chore` | Anything else (dependencies, configuration) |

### Scopes

| Scope | Use it when |
|---|---|
| `assets` | The only thing that changes are images (added, replaced or removed). Say which ones in the description. |
| `scripts` | The change is in `scripts/` |

Without a scope when it affects both or neither (for example, `docs` or `chore`).

Keep image changes in their own commits, apart from the code: it is easier to review, and to go back if one of them was a mistake.

## Adding images

See [`scripts/README.md`](scripts/README.md): `fetch_drivers.py` downloads the ones that are missing and `add_photo.py` adds or replaces one by hand.
