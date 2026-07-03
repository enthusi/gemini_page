#!/usr/bin/env python3

from pathlib import Path
import re
import sys
import shutil

ROOT = Path(".")
SECTIONS = {
    "alice": {
        "dir": ROOT / "alice",
        "prefix": "alice_",
    },
    "neogeo": {
        "dir": ROOT / "neogeo",
        "prefix": "neogeo_",
    },
    "playdate": {
        "dir": ROOT / "playdate",
        "prefix": "voxel_",
    },
}

POST_RE_TEMPLATE = r"^{prefix}(\d{{4}}-\d{{2}}-\d{{2}})\.gmi$"
HOME_INDEX = ROOT / "index.gmi"
HOME_LATEST_COUNT = 12


def extract_title(path):
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    raise ValueError("No top-level '# ' heading found in {}".format(path))


def collect_posts(section_name, section_dir, prefix):
    post_re = re.compile(POST_RE_TEMPLATE.format(prefix=re.escape(prefix)))
    posts = []

    for path in section_dir.iterdir():
        if not path.is_file():
            continue
        if path.name == "index.gmi":
            continue

        m = post_re.match(path.name)
        if not m:
            continue

        date = m.group(1)
        title = extract_title(path)

        posts.append({
            "section": section_name,
            "filename": path.name,
            "date": date,
            "title": title,
        })

    posts.sort(key=lambda p: (p["date"], p["filename"]), reverse=True)
    return posts


def build_section_posts_block(posts):
    lines = ["## posts"]
    for post in posts:
        lines.append("=> {} {} - {}".format(
            post["filename"], post["date"], post["title"]
        ))
    return "\n".join(lines)


def build_home_latest_block(posts, max_count):
    lines = ["## latest posts"]
    for post in posts[:max_count]:
        lines.append("=> {}/{} {} - {}".format(
            post["section"],
            post["filename"],
            post["date"],
            post["title"]
        ))
    return "\n".join(lines)


def replace_named_section(index_text, section_header, new_section_text, index_path):
    lines = index_text.splitlines()

    start = None
    end = None

    for i, line in enumerate(lines):
        if line.strip() == section_header:
            start = i
            break

    if start is None:
        raise ValueError("No '{}' section found in {}".format(section_header, index_path))

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break

    before = "\n".join(lines[:start]).rstrip()
    after = "\n".join(lines[end:]).lstrip()

    if before and after:
        return before + "\n\n" + new_section_text.rstrip() + "\n\n" + after + "\n"
    if before:
        return before + "\n\n" + new_section_text.rstrip() + "\n"
    if after:
        return new_section_text.rstrip() + "\n\n" + after + "\n"
    return new_section_text.rstrip() + "\n"


def backup_file(path):
    backup_path = Path(str(path) + ".bak")
    shutil.copyfile(str(path), str(backup_path))


def write_if_changed(path, old_text, new_text, message):
    if new_text != old_text:
        backup_file(path)
        path.write_text(new_text, encoding="utf-8")
        print(message)
    else:
        print("No changes needed in {}.".format(path))


def update_section_index(section_name, section_dir, prefix):
    index_path = section_dir / "index.gmi"
    if not index_path.exists():
        raise FileNotFoundError("Missing index file: {}".format(index_path))

    posts = collect_posts(section_name, section_dir, prefix)
    new_block = build_section_posts_block(posts)

    old_text = index_path.read_text(encoding="utf-8")
    new_text = replace_named_section(old_text, "## posts", new_block, index_path)

    write_if_changed(
        index_path,
        old_text,
        new_text,
        "Updated {} with {} posts (backup: {}.bak).".format(index_path, len(posts), index_path)
    )

    return posts


def update_home_index(all_posts):
    if not HOME_INDEX.exists():
        raise FileNotFoundError("Missing home index file: {}".format(HOME_INDEX))

    all_posts.sort(key=lambda p: (p["date"], p["filename"]), reverse=True)
    new_block = build_home_latest_block(all_posts, HOME_LATEST_COUNT)

    old_text = HOME_INDEX.read_text(encoding="utf-8")
    new_text = replace_named_section(old_text, "## latest posts", new_block, HOME_INDEX)

    write_if_changed(
        HOME_INDEX,
        old_text,
        new_text,
        "Updated {} with latest posts (backup: {}.bak).".format(HOME_INDEX, HOME_INDEX)
    )


def main():
    try:
        all_posts = []

        for section_name, cfg in SECTIONS.items():
            posts = update_section_index(section_name, cfg["dir"], cfg["prefix"])
            all_posts.extend(posts)

        update_home_index(all_posts)

    except Exception as e:
        print("Error: {}".format(e), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
