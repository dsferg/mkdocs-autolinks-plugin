import logging
import os
import pathlib
import re
from collections import defaultdict
from urllib.parse import quote

from mkdocs.plugins import BasePlugin

LOG = logging.getLogger("mkdocs.plugins." + __name__)

# Regex groups:
# 0: Whole markdown link e.g. [Alt-text](url)
# 1: Alt text
# 2: Full URL e.g. url + hash anchor
# 3: Filename e.g. filename.md
# 4: File extension
# 5: Hash anchor
# 6: Image title
AUTOLINK_RE = (
    r"(?:\!\[\]|\[([^\]]+)\])"
    r"\((([^)/]+\.(md|png|jpg|jpeg|bmp|gif|svg|webp))(#[^)]*)*)(\s(\".*\"))*\)"
)

# Matches the start of a code block
FENCE_RE = re.compile(r"^(```|~~~)")

# Matches a full HTML comment on a single line
INLINE_COMMENT_RE = re.compile(r"()")
COMMENT_START = ""


class AutoLinkReplacer:
    def __init__(self, base_docs_dir, abs_page_path, filename_to_abs_path):
        self.base_docs_dir = base_docs_dir
        self.abs_page_path = abs_page_path
        self.filename_to_abs_path = filename_to_abs_path

    def __call__(self, match):
        filename = match.group(3).strip()

        # Ignore dotfile references silently
        if filename.startswith("."):
            return match.group(0)

        abs_linker_dir = os.path.dirname(self.abs_page_path)

        if filename not in self.filename_to_abs_path:
            # Silent fail allows MkDocs standard linking to take over if needed
            return match.group(0)

        abs_link_paths = self.filename_to_abs_path[filename]
        abs_link_path = abs_link_paths[0]

        rel_link_path = quote(
            pathlib.PurePath(
                os.path.relpath(abs_link_path, abs_linker_dir)
            ).as_posix()
        )

        return match.group(0).replace(match.group(3), rel_link_path)


class AutoLinksPlugin(BasePlugin):
    def __init__(self):
        self.filename_to_abs_path = None

    def on_page_markdown(self, markdown, page, config, files, **kwargs):
        if self.filename_to_abs_path is None:
            self.init_filename_to_abs_path(files)

        base_docs_dir = config["docs_dir"]
        abs_page_path = page.file.abs_src_path
        replacer = AutoLinkReplacer(
            base_docs_dir, abs_page_path, self.filename_to_abs_path
        )

        in_comment = False
        in_fence = False
        output = []

        for line in markdown.splitlines(keepends=True):
            stripped = line.strip()

            # 1. Handle Fenced Code Blocks (Toggle State)
            if FENCE_RE.match(stripped):
                in_fence = not in_fence
                output.append(line)
                continue

            # 2. Skip content if inside a Multi-line Code Block
            if in_fence:
                output.append(line)
                continue

            # 3. Handle Multi-line HTML Comments
            if in_comment:
                output.append(line)
                if COMMENT_END in line:
                    in_comment = False
                continue

            # 4. Handle Start of Multi-line Comment ()
            if COMMENT_START in line and COMMENT_END not in line:
                in_comment = True
                # Process the visible part before the comment starts
                parts = line.split(COMMENT_START, 1)
                processed = re.sub(AUTOLINK_RE, replacer, parts[0])
                output.append(processed + COMMENT_START + parts[1])
                continue

            # 5. Handle Inline Comments (Safe Tokenizing)
            # This splits the line into [text, , text, ]
            parts = INLINE_COMMENT_RE.split(line)
            processed_line = []
            
            for part in parts:
                if part.startswith(COMMENT_START):
                    # It's a comment, append as-is
                    processed_line.append(part)
                else:
                    # It's text, process links
                    processed_line.append(re.sub(AUTOLINK_RE, replacer, part))
            
            output.append("".join(processed_line))

        return "".join(output)

    def init_filename_to_abs_path(self, files):
        self.filename_to_abs_path = defaultdict(list)

        for file_ in files:
            filename = os.path.basename(file_.abs_src_path)

            # Skip dotfiles
            if filename.startswith("."):
                continue

            self.filename_to_abs_path[filename].append(file_.abs_src_path)

        # Report duplicates once per build
        duplicates = {
            name: paths
            for name, paths in self.filename_to_abs_path.items()
            if len(paths) > 1
        }

        if duplicates:
            messages = []
            for filename, paths in duplicates.items():
                messages.append(
                    f"- {filename}:\n    " + "\n    ".join(paths)
                )

            LOG.warning(
                "AutoLinksPlugin found duplicate filenames. "
                "Filename-based autolinks may be ambiguous.\n\n%s",
                "\n".join(messages),
            )