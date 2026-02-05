# MkDocs Autolinks Plugin (Fork)

An MkDocs plugin that simplifies relative linking between documents.

This is a fork of the original **mkdocs-autolinks-plugin** with a small number of behavior changes aimed at improving correctness and predictability in larger documentation sets.

## Differences in this fork

This fork preserves the core behavior of the original plugin, with a few intentional differences:

- Autolinks are not processed inside:

  - fenced code blocks (``` or ~~~)

  - HTML comments (`<!-- ... -->`)

- Files whose filename starts with `.` (dotfiles) are ignored and not considered for link resolution

- If multiple files share the same filename, the build fails with a clear error instead of choosing one arbitrarily

These changes are intended to prevent ambiguous links and unexpected rewrites while keeping the plugin easy to use.

## License

This project inherits the license of the original **mkdocs-autolinks-plugin**.