## What and why

<!-- What does this change do, and why is it needed? Link the issue: "Closes #123". -->

## Related pull requests

<!-- For changes across repositories: link the other pull requests and the merge order (usually backend → frontend → master). Write "None" otherwise. -->

## How it was tested

<!-- Commands you ran and what you checked by hand, for each affected role (admin, owner, manager, customer). -->

## Screenshots

<!-- For UI changes: before and after, in light and dark theme. Delete this section otherwise. -->

## Checklist

- [ ] Follows the [standards](https://github.com/smit9924/hospitia-master/blob/main/docs/standards/index.md) and the closest existing pattern; no unrelated changes.
- [ ] Lint passes (`uv run ruff check .` / `npm run lint`) and frontend tests pass (`npm test`).
- [ ] Database changes have a reviewed Alembic migration with a working downgrade.
- [ ] UI changes pass AXE checks, work in light and dark theme, and are responsive.
- [ ] No secrets, `.env` files or credentials are included.
- [ ] Docs in `hospitia-master/docs/` are updated (or `/doc-sync` was run, if available), and the API reference is regenerated for API changes (`bash scripts/export_openapi.sh`).
- [ ] `CHANGELOG.md` in `hospitia-master` has an `[Unreleased]` entry for user-visible changes.
