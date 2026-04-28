# Publishing OpIndex

This project is prepared for PyPI Trusted Publishing from GitHub Actions.

Do not upload releases manually with `twine upload`. PyPI publication should happen only from GitHub Actions.

## Important naming note

This project is configured to publish under:

```text
opindex
```

The installed command is:

```text
opindex
```

## One-time PyPI setup

1. Create a PyPI account.
2. Create a pending Trusted Publisher for the `opindex` project on PyPI.
3. Point that publisher at:
   - owner: `CameronCandau`
   - repository: `OpIndex`
   - workflow: `publish-pypi.yml`
4. Optionally require a GitHub environment named `pypi`.

References:

- PyPI Trusted Publishing: https://docs.pypi.org/trusted-publishers/
- GitHub OIDC for PyPI: https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-pypi

## Release process

1. Update version metadata in:
   - `pyproject.toml`
   - `cmd_manager/__init__.py`
2. Run tests locally.
3. Commit the release.
4. Push a tag in the form `v<semver>`, for example `v0.1.0`.
5. GitHub Actions will validate the tag against package metadata, then build and publish automatically.

## Local verification

Run tests:

```bash
python3 -m pytest tests/
```

Build locally:

```bash
python3 -m build
```

Check the built metadata locally:

```bash
python3 -m twine check dist/*
```

## Notes

- The publish workflow runs only for pushed tags matching `v<semver>`.
- The workflow validates that the tag version matches both `pyproject.toml` and `cmd_manager/__init__.py`.
- GitHub Releases are optional; they are not the publication trigger.
- The previous GitHub Release `published` trigger is retired and should not be used for future releases.
- The workflow uses OIDC Trusted Publishing and does not need a long-lived PyPI API token.
- Local `build` and `twine check` are for verification only, not publication.
- If `opindex` is unavailable when you finally publish, change the distribution name in `pyproject.toml` and update this document before release.
