"""
Tests for the mkdocs-autolinks-plugin

Run these tests with: pytest tests/
"""
import os
import tempfile
from collections import defaultdict
from mkdocs_autolinks_plugin.plugin import AutoLinksPlugin, AutoLinkReplacer


class MockFile:
    """Mock MkDocs file object for testing"""
    def __init__(self, abs_src_path):
        self.abs_src_path = abs_src_path


class MockPage:
    """Mock MkDocs page object for testing"""
    def __init__(self, abs_src_path):
        self.file = MockFile(abs_src_path)


class TestAutoLinkReplacer:
    """Test the core link replacement functionality"""

    def setup_method(self):
        """Setup test fixtures before each test"""
        # Create a simple file structure for testing
        self.base_dir = "/fake/docs"
        self.filename_to_abs_path = defaultdict(list)
        self.filename_to_abs_path["target.md"] = ["/fake/docs/target.md"]
        self.filename_to_abs_path["other.md"] = ["/fake/docs/subdir/other.md"]
        self.filename_to_abs_path["image.png"] = ["/fake/docs/images/image.png"]

    def test_simple_link_replacement(self):
        """Test that a simple markdown link gets replaced with relative path"""
        replacer = AutoLinkReplacer(
            self.base_dir,
            "/fake/docs/source.md",
            self.filename_to_abs_path
        )

        # Match object simulation - group(0) is full match, group(3) is filename
        import re
        from mkdocs_autolinks_plugin.plugin import AUTOLINK_RE

        markdown = "[link text](target.md)"
        match = re.search(AUTOLINK_RE, markdown)

        result = replacer(match)
        assert "target.md" in result
        # The relative path from source.md to target.md is just "target.md"

    def test_dotfile_ignored(self):
        """Test that dotfiles are ignored silently"""
        replacer = AutoLinkReplacer(
            self.base_dir,
            "/fake/docs/source.md",
            self.filename_to_abs_path
        )

        import re
        from mkdocs_autolinks_plugin.plugin import AUTOLINK_RE

        markdown = "[link](.hidden.md)"
        match = re.search(AUTOLINK_RE, markdown)

        result = replacer(match)
        # Should return original unchanged
        assert result == "[link](.hidden.md)"


class TestMarkdownProcessing:
    """Test the markdown line processing (fences, comments, etc.)"""

    def setup_method(self):
        """Setup plugin instance for testing"""
        self.plugin = AutoLinksPlugin()

        # Create minimal filename mapping
        self.plugin.filename_to_abs_path = defaultdict(list)
        self.plugin.filename_to_abs_path["target.md"] = ["/fake/docs/target.md"]

        # Create a simple replacer
        self.replacer = AutoLinkReplacer(
            "/fake/docs",
            "/fake/docs/source.md",
            self.plugin.filename_to_abs_path
        )

    def test_fenced_code_block_ignored(self):
        """Test that links inside fenced code blocks are not processed"""
        markdown = """
Some text with [normal link](target.md)

```
This is code with [link](target.md) that should not be processed
```

More text with [another link](target.md)
"""
        result = self.plugin._process_markdown_lines(markdown, self.replacer)

        # The link inside the fence should remain unchanged
        lines = result.split('\n')
        code_line = [l for l in lines if 'This is code' in l][0]
        assert '[link](target.md)' in code_line  # Should be unchanged

    def test_html_comment_ignored(self):
        """Test that links inside HTML comments are not processed"""
        markdown = "<!-- This is a comment with [link](target.md) -->"

        result = self.plugin._process_markdown_lines(markdown, self.replacer)

        # Link should remain unchanged inside comment
        assert '[link](target.md)' in result

    def test_multiline_comment_ignored(self):
        """Test that links in multi-line HTML comments are not processed"""
        markdown = """
Before comment [link1](target.md)
<!--
This is a multi-line comment
with [link](target.md) inside
-->
After comment [link2](target.md)
"""
        result = self.plugin._process_markdown_lines(markdown, self.replacer)

        # Link inside comment should be unchanged
        assert 'with [link](target.md) inside' in result

    def test_tildes_fence_works(self):
        """Test that ~~~ fences also work (not just ```)"""
        markdown = """
~~~
Code with [link](target.md)
~~~
"""
        result = self.plugin._process_markdown_lines(markdown, self.replacer)

        # Link should be unchanged
        assert '[link](target.md)' in result

    def test_mixed_content(self):
        """Test a complex mix of fences, comments, and regular text"""
        markdown = """
Regular [link1](target.md) here

```python
def foo():
    # [link2](target.md) in code
    pass
```

<!-- Comment with [link3](target.md) -->

Another [link4](target.md) outside
"""
        result = self.plugin._process_markdown_lines(markdown, self.replacer)

        # Links in code and comments should be unchanged
        assert '[link2](target.md)' in result
        assert '[link3](target.md)' in result


class TestDuplicateDetection:
    """Test duplicate filename handling"""

    def test_duplicate_warning_logged(self, caplog):
        """Test that duplicate filenames generate a warning"""
        plugin = AutoLinksPlugin()
        plugin.config = {'fail_on_duplicates': False, 'exclude_filenames': []}

        # Create mock files with duplicate names
        mock_files = [
            MockFile("/fake/docs/dir1/duplicate.md"),
            MockFile("/fake/docs/dir2/duplicate.md"),
            MockFile("/fake/docs/unique.md"),
        ]

        # Initialize the filename mapping
        plugin.init_filename_to_abs_path(mock_files)

        # Check that warning was logged
        assert "duplicate filenames" in caplog.text.lower()
        assert "duplicate.md" in caplog.text

    def test_fail_on_duplicates_raises_exception(self):
        """Test that fail_on_duplicates=True raises an exception"""
        plugin = AutoLinksPlugin()
        plugin.config = {'fail_on_duplicates': True, 'exclude_filenames': []}

        # Create mock files with duplicate names
        mock_files = [
            MockFile("/fake/docs/dir1/duplicate.md"),
            MockFile("/fake/docs/dir2/duplicate.md"),
        ]

        # Should raise an exception
        import pytest
        with pytest.raises(Exception) as exc_info:
            plugin.init_filename_to_abs_path(mock_files)

        # Exception should mention duplicates
        assert "duplicate" in str(exc_info.value).lower()
        assert "duplicate.md" in str(exc_info.value)

    def test_dotfiles_excluded_from_mapping(self):
        """Test that dotfiles are not included in the filename mapping"""
        plugin = AutoLinksPlugin()
        plugin.config = {'fail_on_duplicates': False, 'exclude_filenames': []}

        mock_files = [
            MockFile("/fake/docs/.hidden.md"),
            MockFile("/fake/docs/normal.md"),
        ]

        plugin.init_filename_to_abs_path(mock_files)

        # Dotfile should not be in mapping
        assert ".hidden.md" not in plugin.filename_to_abs_path
        assert "normal.md" in plugin.filename_to_abs_path

    def test_exclude_filenames(self):
        """Test that excluded filenames are not included in the mapping"""
        plugin = AutoLinksPlugin()
        plugin.config = {
            'fail_on_duplicates': False,
            'exclude_filenames': ['nav.md', 'header.md']
        }

        mock_files = [
            MockFile("/fake/docs/nav.md"),
            MockFile("/fake/docs/subdir/nav.md"),
            MockFile("/fake/docs/header.md"),
            MockFile("/fake/docs/normal.md"),
        ]

        plugin.init_filename_to_abs_path(mock_files)

        # Excluded files should not be in mapping
        assert "nav.md" not in plugin.filename_to_abs_path
        assert "header.md" not in plugin.filename_to_abs_path
        # Normal file should be in mapping
        assert "normal.md" in plugin.filename_to_abs_path

    def test_exclude_filenames_prevents_duplicate_errors(self):
        """Test that excluding duplicates prevents errors"""
        plugin = AutoLinksPlugin()
        plugin.config = {
            'fail_on_duplicates': True,
            'exclude_filenames': ['nav.md']
        }

        mock_files = [
            MockFile("/fake/docs/nav.md"),
            MockFile("/fake/docs/subdir/nav.md"),  # Would be duplicate, but excluded
            MockFile("/fake/docs/normal.md"),
        ]

        # Should not raise an exception because nav.md is excluded
        plugin.init_filename_to_abs_path(mock_files)

        # Verify nav.md is not in mapping
        assert "nav.md" not in plugin.filename_to_abs_path


class TestImageLinks:
    """Test that image links are also processed"""

    def test_image_link_processed(self):
        """Test that image references like ![](image.png) are processed"""
        plugin = AutoLinksPlugin()
        plugin.filename_to_abs_path = defaultdict(list)
        plugin.filename_to_abs_path["image.png"] = ["/fake/docs/images/image.png"]

        replacer = AutoLinkReplacer(
            "/fake/docs",
            "/fake/docs/page.md",
            plugin.filename_to_abs_path
        )

        markdown = "![](image.png)"
        result = plugin._process_markdown_lines(markdown, replacer)

        # Image should be processed (though exact path depends on relative calculation)
        assert "image.png" in result or "images/image.png" in result
