import os
import re
import pytest

# Regex patterns for Markdown links and images
LINK_PATTERN = re.compile(r'\[.*?\]\((.*?)\)')  # Matches [text](link)
IMAGE_PATTERN = re.compile(r'!\[.*?\]\((.*?)\)')  # Matches ![text](image)

def extract_links_and_images(filepath):
    """Extract all links and image paths from a markdown file."""
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()
    links = LINK_PATTERN.findall(content)
    images = IMAGE_PATTERN.findall(content)
    return links + images

def strip_anchor(link):
    """Remove anchor (e.g., #section) from a link."""
    return link.split('#')[0]

def is_valid_local_path(base_path, target_path):
    """Check if a local path exists relative to the base path."""
    # Resolve full path
    full_path = os.path.normpath(os.path.join(base_path, target_path))
    return os.path.exists(full_path)

def find_all_markdown_links(start_file):
    """Recursively find all Markdown files and validate their links."""
    visited = set()  # To avoid revisiting files
    broken_links = []

    def process_file(filepath):
        """Process a single Markdown file."""
        if filepath in visited:
            return  # Avoid revisiting files
        visited.add(filepath)

        base_path = os.path.dirname(filepath)
        items = extract_links_and_images(filepath)

        for item in items:
            # Ignore external links
            if item.startswith("http"):
                continue

            item = strip_anchor(item)

            # Validate local links
            item_path = os.path.normpath(os.path.join(base_path, item))
            if not os.path.exists(item_path):
                broken_links.append((filepath, item))
            elif item.endswith(".md"):
                # Recurse into linked Markdown files
                process_file(item_path)

    # Start with the index file
    process_file(start_file)
    return broken_links

@pytest.mark.parametrize("start_file", ["docs/index.md"])
def test_recursive_markdown_links(start_file):
    """Test links recursively starting from index.md."""
    assert os.path.exists(start_file), f"Start file {start_file} does not exist"
    broken_links = find_all_markdown_links(start_file)
    assert not broken_links, f"Broken links found: {broken_links}"

