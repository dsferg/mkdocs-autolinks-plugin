import logging
import os
import pathlib
import re
from collections import defaultdict
from urllib.parse import quote

from mkdocs.plugins import BasePlugin

LOG = logging.getLogger("mkdocs.plugins." + __name__)

# Match HTML anchor/image tags with relative file references
# We only rewrite links that point to local filenames
HTML_LINK_RE = re.compile(
    r'href="([^":]+?\.(md|png|jpg|jpeg|bmp|gif|svg|webp))(#[^"]*)?"'
)

class AutoLinksPlugin(BasePlugin):
    def __init__(self):
        self.filename_to_abs_path = None

    def on_files(self, files, config):
        """
        Build filename lookup once at start.
        """
        self.filename_to_abs_path = defaultdict(list)
        for file_ in files:
            filename = os.path.basename(file_.abs_src_path)
            self.filename_to_abs_path[filename].append(file_.abs_src_path)

    def on_page_content(self, html, page, config, files):
        """
        Run AFTER macros + markdown conversion.
        Now we operate safely on HTML.
        """

        base_docs_dir = config["docs_dir"]
        abs_page_path = page.file.abs_src_path
        abs_linker_dir = os.path.dirname(abs_page_path)

        def replacer(match):
            filename = os.path.basename(match.group(1))

            if filename not in self.filename_to_abs_path:
                LOG.warning(
                    "AutoLinksPlugin unable to find %s in directory %s",
                    filename,
                    base_docs_dir,
                )
                return match.group(0)

            abs_link_paths = self.filename_to_abs_path[filename]

            if len(abs_link_paths) > 1:
                LOG.warning(
                    "AutoLinksPlugin: Duplicate filename referred to in '%s': '%s' exists at %s",
                    abs_page_path,
                    filename,
                    abs_link_paths,
                )

            abs_link_path = abs_link_paths[0]
            rel_link_path = quote(
                pathlib.PurePath(
                    os.path.relpath(abs_link_path, abs_linker_dir)
                ).as_posix()
            )

            anchor = match.group(3) or ""
            return f'href="{rel_link_path}{anchor}"'

        # Only process links outside HTML comments
        result = []
        in_comment = False

        for line in html.splitlines(keepends=True):
            if "<!--" in line:
                in_comment = True

            if in_comment:
                result.append(line)
                if "-->" in line:
                    in_comment = False
                continue

            processed = HTML_LINK_RE.sub(replacer, line)
            result.append(processed)

        return "".join(result)
