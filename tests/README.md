# Tests for mkdocs-autolinks-plugin

## Running Tests (Easiest Method)

Use the automated script that handles everything for you:

```bash
./run_tests.sh
```

This script will:
- Create a virtual environment (if it doesn't exist)
- Install all dependencies
- Run the tests
- Clean up when done

## Manual Method (Using Virtual Environment)

If you prefer to run tests manually:

### First Time Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
pip install -e .
```

### Running Tests

```bash
# Activate venv (if not already active)
source venv/bin/activate

# Run tests
python -m pytest tests/ -v

# When done, deactivate
deactivate
```

## Without Virtual Environment (Not Recommended)

If you must install globally:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pip install -e .
python3 -m pytest tests/ -v
```

## What the Tests Cover

The test suite includes:

1. **Basic link replacement** - Verifies simple autolinks work
2. **Fenced code blocks** - Ensures links in ``` or ~~~ blocks are ignored
3. **HTML comments** - Ensures links in <!-- --> are ignored
4. **Multi-line comments** - Handles comments spanning multiple lines
5. **Dotfile handling** - Verifies .dotfiles are ignored
6. **Duplicate detection** - Checks that duplicate filenames log warnings
7. **Image links** - Verifies images like ![](image.png) are processed
8. **Mixed content** - Complex scenarios with multiple features

## Understanding Test Output

✅ **PASSED** = Test succeeded (green checkmark)
❌ **FAILED** = Test failed (shows what went wrong)

Example output:
```
tests/test_plugin.py::TestMarkdownProcessing::test_fenced_code_block_ignored PASSED
tests/test_plugin.py::TestMarkdownProcessing::test_html_comment_ignored PASSED

10 passed in 0.38s
```

All green = Everything works! 🎉
