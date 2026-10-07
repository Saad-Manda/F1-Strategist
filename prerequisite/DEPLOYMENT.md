# Static delivery

The local delivery artifact is `dist/rl-prerequisites-static.zip`. Extract its contents
into a static host's document root, or a directory such as `/site/`. `index.html` is
the entry point. Publish only the archive contents or the equivalent `site/` tree.
Authoring sources, scripts, tests, environments and project plans stay outside it.

No build step, Python process, Node server or backend is required on the host.
Preserve filenames and relative paths, including exercise ZIPs and recorded fixtures.
Serve missing files as 404; do not configure an SPA fallback. Serve JavaScript with
a JavaScript MIME type and JSON as `application/json`.

For local verification from `prerequisite/`:

```powershell
python scripts/check_project.py
python scripts/check_course_v2.py --publish
python scripts/build_static_delivery.py --write
python scripts/build_static_delivery.py
python scripts/preview.py
python scripts/preview.py --port 8001 --subdirectory
```

The archive is reproducible for identical source bytes. The reading registry and
runtime assets must be released together; HTML and module imports share one cache
version. During replacement, close or reload older course tabs before retaining
progress. Existing v1 data and the first migration backup remain recoverable.

Progress is browser localStorage on the hosting origin. Export/import is required
when moving to another origin; a downloaded Python pack does not synchronize progress.
Completion saving needs JavaScript and an exclusive browser storage lock. Static
reading links and exercise downloads remain usable without JavaScript.

Local packaging does not deploy the site. Hosting publication, Git staging, commits
and pushes require a separate user instruction. See the current
[delivery review](content/R8_REVIEW.md) for counts, validation and limitations.
