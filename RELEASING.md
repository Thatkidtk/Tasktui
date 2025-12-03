# Releasing Tasktui

1) Update version
- Set the new version in `pyproject.toml`.
- Update `CHANGELOG.md` with highlights.

2) Verify
- `pip install -e ".[dev]"`
- `ruff check .`
- `mypy .`
- `pytest`

3) Tag
- `git commit -am "Release vX.Y.Z"`
- `git tag -a vX.Y.Z -m "vX.Y.Z"`
- `git push origin main vX.Y.Z`

4) GitHub Release
- Draft a release on https://github.com/Thatkidtk/Tasktui/releases/new using the tag.
- Attach notes from `CHANGELOG.md`.

5) pipx recipe
- Users can install the tagged release directly:
  - `pipx install git+https://github.com/Thatkidtk/Tasktui.git@vX.Y.Z`

6) Announce
- Add a screenshot/asciinema link to the release notes.
