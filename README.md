# MkDocs Autolinks Plugin (Fork)

An MkDocs plugin that simplifies relative linking between documents.

This is a fork of the original **mkdocs-autolinks-plugin** with a small number of behavior changes aimed at improving correctness and predictability in larger documentation sets.

## Differences in this fork

This fork preserves the core behavior of the original plugin, with a few intentional differences:

- Autolinks are not processed inside:

  - fenced code blocks (``` or ~~~)

  - HTML comments (`<!-- ... -->`)

- Files whose filename starts with `.` (dotfiles) are ignored and not considered for link resolution

- If multiple files share the same filename, a warning is logged and the first file is used (instead of silently choosing one arbitrarily)

These changes are intended to prevent ambiguous links and unexpected rewrites while keeping the plugin easy to use.

## Configuration

The plugin supports the following configuration option in your `mkdocs.yml`:

```yaml
plugins:
  - autolinks:
      fail_on_duplicates: false  # Default is false
```

### Options

- **`fail_on_duplicates`** (boolean, default: `false`):
  - When `false`: Logs a warning when duplicate filenames are found and uses the first file
  - When `true`: Fails the build with an error when duplicate filenames are found

## License

This project inherits the license of the original **mkdocs-autolinks-plugin**.