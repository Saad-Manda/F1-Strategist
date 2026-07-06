# Auto-generate Rules Command

This command analyzes the current codebase, directories, and files to generate or update `ANTIGRAVITY.md` in the project root.

## Execution Steps

1. List all directories and key configuration files.
2. Auto-detect project tech stack, frameworks, package managers, and configuration files (e.g., `package.json`, `requirements.txt`).
3. Compile findings and construct/update the `ANTIGRAVITY.md` file using the template in `.antigravity/ANTIGRAVITY-template.md`.
