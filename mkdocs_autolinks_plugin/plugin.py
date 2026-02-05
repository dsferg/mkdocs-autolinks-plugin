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

FENCE_RE = re.compile(r"^(```|~~~)")
COMMENT_START = "<!--"
COMMENT_END = "-->"


class AutoLinkReplacer:
    def __init__(self, base_docs_dir, abs_page_path, filename_to_abs_path):
        self.base_docs_dir = base_docs_dir
        self.abs_page_path = abs_page_path
        self.filename_to_abs_path = filename_to_abs_path

    def __call__(self, match):
        filename = match.group(3).strip()
        abs_linker_dir = os.path.dirname(self.abs_page_path)

        if filename not in self.filename_to_abs_path:
            LOG.warning(
                "AutoLinksPlugin unable to find %s in directory %s",
                filename,
                self.base_docs_dir,
            )
            return match.group(0)

        abs_link_paths = self.filename_to_abs_path[filename]

        if len(abs_link_paths) > 1:
            LOG.warning(
                "AutoLinksPlugin: Duplicate filename referred to in '%s': '%s' exists at %s",
                self.abs_page_path,
                filename,
                abs_link_paths,
            )

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

            # Toggle fenced code blocks
            if FENCE_RE.match(stripped):
                in_fence = not in_fence
                output.append(line)
                continue

            # Enter comment block
            if COMMENT_START in line and not in_comment:
                in_comment = True
                output.append(line)
                if COMMENT_END in line:
                    in_comment = False
                continue

            # Inside comment block
            if in_comment:
                output.append(line)
                if COMMENT_END in line:
                    in_comment = False
                continue

            # Inside fenced code block
            if in_fence:
                output.append(line)
                continue

            # Safe to process autolinks
            processed = re.sub(AUTOLINK_RE, replacer, line)
            output.append(processed)

        return "".join(output)

    def init_filename_to_abs_path(self, files):
        self.filename_to_abs_path = defaultdict(list)
        for file_ in files:
            filename = os.path.basename(file_.abs_src_path)

            # Skip dotfiles (excluded from the build)
            if filename.startswith("."):
                continue

            self.filename_to_abs_path[filename].append(file_.abs_src_path)
