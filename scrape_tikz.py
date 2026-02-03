#!/usr/bin/env python3
"""
Scraper for TikZ examples from TeXample.net
Downloads TikZ code and metadata from the gallery
"""

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class TikZScraper:
    def __init__(self, output_dir="library"):
        self.base_url = "https://texample.net"
        self.gallery_url = f"{self.base_url}/tikz/examples/all/"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (TikZ Library Builder)"})

    def get_example_links(self, max_pages=None):
        """Get all example links from the gallery"""
        print("Fetching example links from gallery...")
        example_links = []
        page = 1

        while True:
            if max_pages and page > max_pages:
                break

            url = f"{self.gallery_url}?page={page}" if page > 1 else self.gallery_url
            print(f"  Fetching page {page}...")

            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"  Error fetching page {page}: {e}")
                break

            soup = BeautifulSoup(response.text, "html.parser")

            # Find example links (they're in article titles)
            articles = soup.find_all("article")
            if not articles:
                print(f"  No more examples found on page {page}")
                break

            for article in articles:
                title_link = article.find("h2", class_="entry-title")
                if title_link and title_link.find("a"):
                    link = title_link.find("a")["href"]
                    full_link = urljoin(self.base_url, link)
                    example_links.append(full_link)

            print(f"  Found {len(articles)} examples on page {page}")

            # Check if there's a next page
            next_link = soup.find("a", {"rel": "next"})
            if not next_link:
                break

            page += 1
            time.sleep(0.5)  # Be polite

        print(f"\nTotal examples found: {len(example_links)}")
        return example_links

    def extract_tikz_code(self, soup):
        """Extract TikZ code from the example page"""
        # Look for code blocks
        code_blocks = soup.find_all(["pre", "code"])

        for block in code_blocks:
            text = block.get_text()
            # Check if it looks like LaTeX/TikZ code
            if "\\documentclass" in text or "\\begin{tikzpicture}" in text:
                return text.strip()

        return None

    def extract_metadata(self, soup, url):
        """Extract metadata from the example page"""
        metadata = {"url": url}

        # Title
        title_elem = soup.find("h1", class_="entry-title")
        if not title_elem:
            title_elem = soup.find("h1")
        if title_elem:
            metadata["title"] = title_elem.get_text().strip()

        # Author
        author_elem = soup.find("span", class_="username")
        if author_elem:
            metadata["author"] = author_elem.get_text().strip()

        # Date
        date_elem = soup.find("time")
        if date_elem:
            metadata["date"] = date_elem.get("datetime") or date_elem.get_text().strip()

        # Tags
        tags = []
        tag_elems = soup.find_all("a", href=re.compile(r"/tikz/tag/"))
        for tag in tag_elems:
            tags.append(tag.get_text().strip())
        if tags:
            metadata["tags"] = tags

        # Categories
        categories = []
        cat_elems = soup.find_all("a", href=re.compile(r"/tikz/examples/category/"))
        for cat in cat_elems:
            categories.append(cat.get_text().strip())
        if categories:
            metadata["categories"] = categories

        return metadata

    def sanitize_filename(self, text):
        """Create a safe filename from text"""
        # Remove or replace invalid characters
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "-", text)
        return text.lower()[:50]  # Limit length

    def download_example(self, url, index):
        """Download a single example"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"  Error: {e}")
            return False

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract code and metadata
        code = self.extract_tikz_code(soup)
        metadata = self.extract_metadata(soup, url)

        if not code:
            print("  Warning: No TikZ code found")
            return False

        # Create filename
        title = metadata.get("title", f"example-{index:04d}")
        filename = f"{index:04d}-{self.sanitize_filename(title)}"

        # Save .tex file
        tex_file = self.output_dir / f"{filename}.tex"
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(code)

        # Save metadata
        json_file = self.output_dir / f"{filename}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"  ✓ Saved: {filename}")
        return True

    def scrape(self, max_pages=None, max_examples=None):
        """Main scraping function"""
        print("Starting TikZ gallery scraper")
        print(f"Output directory: {self.output_dir.absolute()}\n")

        # Get all example links
        links = self.get_example_links(max_pages)

        if max_examples:
            links = links[:max_examples]

        print(f"\nDownloading {len(links)} examples...")
        print("-" * 60)

        success_count = 0
        for i, link in enumerate(links, 1):
            print(f"[{i}/{len(links)}] {link}")
            if self.download_example(link, i):
                success_count += 1
            time.sleep(0.5)  # Be polite to the server

        print("-" * 60)
        print(f"\n✓ Successfully downloaded {success_count}/{len(links)} examples")
        print(f"Files saved to: {self.output_dir.absolute()}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape TikZ examples from TeXample.net")
    parser.add_argument(
        "--output",
        "-o",
        default="library",
        help="Output directory for downloaded examples (default: library)",
    )
    parser.add_argument("--max-pages", type=int, help="Maximum number of gallery pages to scrape")
    parser.add_argument("--max-examples", type=int, help="Maximum number of examples to download")

    args = parser.parse_args()

    scraper = TikZScraper(output_dir=args.output)
    scraper.scrape(max_pages=args.max_pages, max_examples=args.max_examples)
