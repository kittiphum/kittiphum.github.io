from __future__ import annotations

import argparse
import html
import re
import unicodedata
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


ATOM = "{http://www.w3.org/2005/Atom}"
BLOGGER = "{http://schemas.google.com/blogger/2018}"


class BloggerHtmlToMarkdown(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.link_stack: list[dict[str, str | bool]] = []
        self.skip_stack: list[str] = []
        self.list_stack: list[str] = []
        self.in_pre = False

    def text(self) -> str:
        text = "".join(self.parts)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"

    def append(self, value: str) -> None:
        if not self.skip_stack:
            self.parts.append(value)

    def ensure_blank_line(self) -> None:
        if not self.parts:
            return
        current = "".join(self.parts)
        if current.endswith("\n\n"):
            return
        if current.endswith("\n"):
            self.append("\n")
        else:
            self.append("\n\n")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()

        if tag in {"script", "style"}:
            self.skip_stack.append(tag)
            return
        if tag in {"p", "div", "section", "article", "header", "footer"}:
            self.ensure_blank_line()
        elif tag == "br":
            self.append("\n")
        elif tag in {"strong", "b"}:
            self.append("**")
        elif tag in {"em", "i"}:
            self.append("*")
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.ensure_blank_line()
            self.append("#" * int(tag[1]) + " ")
        elif tag == "blockquote":
            self.ensure_blank_line()
            self.append("> ")
        elif tag == "pre":
            self.ensure_blank_line()
            self.in_pre = True
            self.append("```\n")
        elif tag == "code" and not self.in_pre:
            self.append("`")
        elif tag in {"ul", "ol"}:
            self.list_stack.append(tag)
            self.ensure_blank_line()
        elif tag == "li":
            marker = "1. " if self.list_stack and self.list_stack[-1] == "ol" else "- "
            self.append("\n" + marker)
        elif tag == "a":
            self.link_stack.append(
                {"href": attrs_dict.get("href", ""), "opened": False, "consumed": False}
            )
        elif tag == "img":
            src = attrs_dict.get("src", "").strip()
            alt = attrs_dict.get("alt", "").strip()
            if src:
                image = f"![{escape_link_text(alt)}]({src})"
                if self.link_stack and self.link_stack[-1].get("href"):
                    href = str(self.link_stack[-1]["href"])
                    self.append(f"[{image}]({href})")
                    self.link_stack[-1]["consumed"] = True
                else:
                    self.append(image)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.skip_stack and self.skip_stack[-1] == tag:
            self.skip_stack.pop()
            return
        if self.skip_stack:
            return
        if tag in {"p", "div", "section", "article", "header", "footer", "blockquote"}:
            self.ensure_blank_line()
        elif tag in {"strong", "b"}:
            self.append("**")
        elif tag in {"em", "i"}:
            self.append("*")
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.ensure_blank_line()
        elif tag == "pre":
            self.in_pre = False
            self.append("\n```\n\n")
        elif tag == "code" and not self.in_pre:
            self.append("`")
        elif tag in {"ul", "ol"}:
            if self.list_stack:
                self.list_stack.pop()
            self.ensure_blank_line()
        elif tag == "a":
            link = self.link_stack.pop() if self.link_stack else None
            if link and link.get("opened") and link.get("href"):
                self.append(f"]({link['href']})")

    def handle_data(self, data: str) -> None:
        if self.skip_stack:
            return
        if self.link_stack and self.link_stack[-1].get("href") and not self.link_stack[-1].get("consumed"):
            if not self.link_stack[-1].get("opened"):
                self.append("[")
                self.link_stack[-1]["opened"] = True
            self.append(escape_link_text(data))
            return
        if self.link_stack and self.link_stack[-1].get("consumed"):
            return
        self.append(data if self.in_pre else normalize_space(data))


def escape_link_text(value: str) -> str:
    return value.replace("[", "\\[").replace("]", "\\]")


def normalize_space(value: str) -> str:
    value = value.replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", value)


def html_to_markdown(value: str) -> str:
    parser = BloggerHtmlToMarkdown()
    parser.feed(html.unescape(value or ""))
    parser.close()
    markdown = parser.text()
    markdown = re.sub(r"\n +", "\n", markdown)
    return markdown


def yaml_string(value: str) -> str:
    return "'" + value.replace("'", "''").replace("\n", " ").strip() + "'"


def slugify(value: str, fallback: str) -> str:
    value = unquote(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[-\s_]+", "-", value, flags=re.UNICODE).strip("-")
    return value or fallback


def entry_slug(entry: ET.Element, index: int) -> str:
    for link in entry.findall(f"{ATOM}link"):
        if link.attrib.get("rel") == "alternate":
            path = urlparse(link.attrib.get("href", "")).path
            stem = Path(path).stem
            if stem:
                return slugify(stem, f"post-{index:03d}")
    title = entry.findtext(f"{ATOM}title") or ""
    entry_id = entry.findtext(f"{ATOM}id") or f"post-{index:03d}"
    fallback = re.sub(r"\D+", "", entry_id)[-12:] or f"post-{index:03d}"
    return slugify(title, fallback)


def convert(feed_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    tree = ET.parse(feed_path)
    root = tree.getroot()
    entries = root.findall(f"{ATOM}entry")
    live_posts = [
        entry
        for entry in entries
        if entry.findtext(f"{BLOGGER}type") == "POST"
        and entry.findtext(f"{BLOGGER}status") == "LIVE"
    ]

    used_slugs: set[str] = set()
    for index, entry in enumerate(live_posts, 1):
        title = entry.findtext(f"{ATOM}title") or "Untitled"
        date = entry.findtext(f"{ATOM}published") or entry.findtext(f"{ATOM}updated") or ""
        content = entry.findtext(f"{ATOM}content") or ""
        tags = [
            category.attrib.get("term", "").strip()
            for category in entry.findall(f"{ATOM}category")
            if category.attrib.get("term", "").strip()
        ]

        slug = entry_slug(entry, index)
        base_slug = slug
        counter = 2
        while slug in used_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1
        used_slugs.add(slug)

        front_matter = [
            "---",
            f"title: {yaml_string(title)}",
            f"date: {yaml_string(date)}",
            "tags: [" + ", ".join(yaml_string(tag) for tag in tags) + "]",
            'featured_image: ""',
            'description: ""',
            "---",
            "",
        ]
        body = html_to_markdown(content)
        (output_dir / f"{slug}.md").write_text(
            "\n".join(front_matter) + body,
            encoding="utf-8",
            newline="\n",
        )
    return len(live_posts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("feed", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    count = convert(args.feed, args.output_dir)
    print(f"Converted {count} Blogger posts")


if __name__ == "__main__":
    main()
