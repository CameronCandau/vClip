# Publishing

This repository publishes the `opindex` package to PyPI from GitHub Actions using Trusted Publishing.

## Release Checklist

1. Update the version in:
   - `pyproject.toml`
   - `cmd_manager/__init__.py`
2. Run local checks:

```bash
nix develop -c pytest -q
nix develop -c python -m build --no-isolation
```

3. Commit the release changes.
4. Push a tag in the form `v<semver>`, for example `v0.1.3`.
5. GitHub Actions builds and publishes the release.

## PyPI Setup

Set up a Trusted Publisher for the `opindex` project on PyPI that points at this repository and the `publish-pypi.yml` workflow.

References:

- PyPI Trusted Publishing: https://docs.pypi.org/trusted-publishers/
- GitHub OIDC for PyPI: https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-pypi

## Notes

- The publish workflow runs only for pushed tags matching `v<semver>`.
- The workflow validates the tag against the package version before publishing.
- GitHub Releases are optional; tags are the publication trigger.
- Manual `twine upload` is not part of the release flow.
