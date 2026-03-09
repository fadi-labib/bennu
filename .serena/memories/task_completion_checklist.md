# Task Completion Checklist

When a coding task is completed, do the following:

1. **Run tests:** `cd sim && make test-unit` (for Python changes)
2. **Verify syntax:** `python3 -c "import ast; ast.parse(open('file.py').read())"` for new files
3. **Validate compose:** `docker compose -f <file>.yml config` for Docker changes
4. **Commit:** Use conventional commit messages, no Co-Authored-By
5. **Push:** Always push after committing
6. **Check CI:** `gh run list` to verify workflows pass

## For simulation changes
- Test all affected make targets
- Verify no orphan container warnings
- Check container names don't collide across compose files

## For documentation changes
- Verify mkdocs builds: `mkdocs build` (from repo root)
- Check for stale references to renamed/deleted files
