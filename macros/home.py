from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import yaml
from mkdocs.structure.nav import Navigation, Page


def define_env(env):
    chatter = env.start_chatting("latest-pages")

    def load_source(page: Page) -> Tuple[Dict, List[str]]:
        src_path = getattr(page.file, "abs_src_path", None)
        if not src_path:
            return {}, []
        try:
            text = Path(src_path).read_text(encoding="utf-8")
        except FileNotFoundError:
            chatter(f"Source not found for {page.file.src_path}")
            return {}, []
        lines = text.splitlines()
        front_meta: Dict = {}
        body_start = 0
        if lines and lines[0].strip() == "---":
            front_lines: List[str] = []
            for index, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    body_start = index + 1
                    break
                front_lines.append(line)
            else:
                body_start = len(lines)
            if front_lines:
                try:
                    front_meta = yaml.safe_load("\n".join(front_lines)) or {}
                except yaml.YAMLError as exc:
                    chatter(f"Failed to parse front matter for {page.file.src_path}: {exc}")
        body_lines = lines[body_start:]
        return front_meta, body_lines

    def extract_page_info(page: Page) -> Tuple[Optional[datetime], str, str, bool]:
        page_meta = getattr(page, "meta", {}) or {}
        front_meta, body_lines = load_source(page)
        src_path = getattr(page.file, "abs_src_path", None)
        memo_summary = ""
        if src_path:
            memo_path = Path(src_path).with_suffix(".memo")
            if memo_path.exists():
                try:
                    raw_memo = memo_path.read_text(encoding="utf-8")
                except OSError as exc:
                    chatter(f"Failed to read memo for {page.file.src_path}: {exc}")
                else:
                    memo_summary = " ".join(line.strip() for line in raw_memo.splitlines() if line.strip())
        has_memo = bool(memo_summary)
        raw_date = page_meta.get("date") or front_meta.get("date")
        if raw_date:
            if isinstance(raw_date, datetime):
                page_date = raw_date
            else:
                try:
                    page_date = datetime.fromisoformat(str(raw_date))
                except ValueError:
                    chatter(f"Skip page {page.file.src_path}: invalid date '{raw_date}'")
                    page_date = None
        else:
            page_date = None

        title = page_meta.get("title") or front_meta.get("title") or ""
        if not title:
            auto_title = (page.title or "").strip()
            stem = Path(page.file.src_path).stem.lower()
            if auto_title and auto_title.lower() != stem:
                title = auto_title
        if not title:
            for line in body_lines:
                stripped = line.strip()
                if stripped.startswith("#"):
                    title = stripped.lstrip("# ")
                    break
        if not title:
            title = Path(page.file.src_path).stem

        description = page_meta.get("description") or front_meta.get("description") or ""
        if not description:
            for line in body_lines:
                stripped = line.strip()
                if stripped.startswith("#"):
                    candidate = stripped.lstrip("# ").strip()
                    if candidate:
                        description = candidate
                        break
        if memo_summary:
            description = memo_summary
        return page_date, title.strip(), description.strip(), has_memo

    def resolve_category_label(page: Page, slug: str) -> str:
        if page.ancestors:
            nav_title = page.ancestors[0].title or ""
            if nav_title and "\ufffd" not in nav_title:
                return nav_title
        parts = slug.split("-")
        if len(parts) >= 5 and parts[-2].isdigit() and parts[-1].isdigit():
            base = "-".join(parts[:-2])
            year = parts[-2]
            month = parts[-1]
            base_label = base
            try:
                month_value = int(month)
                month_label = f"{month_value:02d}月"
            except ValueError:
                month_label = f"{month}月"
            return f"{base_label} {year}年{month_label}"
        return slug

    def iter_dated_pages(pages: Iterable[Page]):
        for page in pages:
            page_date, title, description, has_memo = extract_page_info(page)
            if page_date is None:
                continue
            yield page_date, title, description, page, has_memo

    def collect_entries(navigation: Navigation):
        entries = []
        for page_date, title, description, page, has_memo in iter_dated_pages(navigation.pages):
            src_uri = getattr(page.file, "src_uri", "")
            if not src_uri:
                continue
            category_slug = src_uri.split("/", 1)[0]
            category_label = resolve_category_label(page, category_slug)
            entries.append({
                "date": page_date,
                "title": title,
                "description": description,
                "url": src_uri,
                "category_slug": category_slug,
                "category_label": category_label,
                "has_memo": has_memo,
            })
        entries.sort(key=lambda item: item["date"], reverse=True)
        return entries

    def read_nav_category_order() -> Dict[str, int]:
        config = env.variables.get("config", {}) or {}
        docs_dir = Path(config.get("docs_dir", "docs"))
        pages_path = docs_dir / ".pages"
        try:
            root_pages = yaml.safe_load(pages_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as exc:
            chatter(f"Failed to read root .pages for category order: {exc}")
            return {}

        category_order: Dict[str, int] = {}
        for item in root_pages.get("nav", []):
            if isinstance(item, str):
                continue
            if not isinstance(item, dict):
                continue
            for children in item.values():
                if not isinstance(children, list):
                    continue
                for child in children:
                    if isinstance(child, str):
                        slug = child
                    elif isinstance(child, dict):
                        slug = str(child.get("path", ""))
                    else:
                        continue
                    if slug:
                        category_order.setdefault(slug, len(category_order))
        return category_order

    def build_entry_line(entry: Dict) -> str:
        date_text = entry["date"].strftime("%Y-%m-%d")
        line = f"- [{date_text}]({entry['url']})"
        if entry.get("has_memo") and entry["description"]:
            desc = " ".join(entry["description"].split())
            if len(desc) > 120:
                desc = desc[:117].rstrip() + "..."
            line += f" - {desc}"
        elif entry["title"]:
            line += f" - {entry['title']}"
        return line

    @env.macro
    def latest_pages(limit: int = 5):
        navigation: Navigation | None = env.variables.get("navigation")
        if navigation is None:
            chatter("No navigation available yet")
            return ""
        entries = collect_entries(navigation)
        seen = set()
        rows: List[str] = []
        for entry in entries:
            if entry["url"] in seen:
                continue
            seen.add(entry["url"])
            rows.append(build_entry_line(entry))
            if len(rows) >= limit:
                break
        return "\n".join(rows)

    @env.macro
    def home_sections(per_category: int = 5, max_categories: Optional[int] = None):
        navigation: Navigation | None = env.variables.get("navigation")
        if navigation is None:
            chatter("No navigation available yet")
            return ""
        category_order = read_nav_category_order()
        entries = collect_entries(navigation)
        categories: Dict[str, Dict[str, object]] = {}
        for entry in entries:
            slug = entry["category_slug"]
            bucket = categories.setdefault(slug, {
                "label": entry["category_label"],
                "slug": slug,
                "items": [],
                "seen": set(),
            })
            if entry["url"] in bucket["seen"]:
                continue
            if len(bucket["items"]) >= per_category:
                continue
            bucket["items"].append(entry)
            bucket["seen"].add(entry["url"])
        ordered_categories = sorted(
            (data for data in categories.values() if data["items"]),
            key=lambda data: (
                data["items"][0]["date"],
                -category_order.get(str(data["slug"]), len(category_order)),
            ),
            reverse=True,
        )
        if max_categories is not None:
            ordered_categories = ordered_categories[:max_categories]
        sections: List[str] = []
        for data in ordered_categories:
            lines = [f"### {data['label']}", ""]
            for item in data["items"]:
                lines.append(build_entry_line(item))
            sections.append("\n".join(lines))
        return "\n\n".join(sections)
