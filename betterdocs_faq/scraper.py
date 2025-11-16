#!/usr/bin/env python

import argparse
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Mapping, Optional, Tuple

from bs4 import BeautifulSoup
from bs4.element import CData, Comment, Declaration, Doctype, NavigableString, ProcessingInstruction, Tag
from jinja2 import Environment, PackageLoader, select_autoescape

from .util.legal import require_user_consent


_base_dir = Path(__file__).parent
_cwd = Path(os.getcwd())
_script_file = Path(__file__).name
_script_name = os.path.splitext(_script_file)[0]


logger = logging.getLogger(__name__)


_template_env = None
def template_env() -> Environment:
    global _template_env
    if not isinstance(_template_env, Environment):
        _template_env = Environment(
            loader=PackageLoader(_base_dir.name),
            autoescape=select_autoescape(),
        )
    return _template_env


def clean_path(path: os.PathLike) -> str:
    path_str = str(path)
    prefixes = [
        str(_base_dir),
        str(_cwd),
    ]
    for prefix in prefixes:
        path_str = path_str[len(prefix):] if path_str.startswith(prefix) else path_str
    return path_str


def clean_node(node):
    if isinstance(node, NavigableString):
        return
    if len(node.contents) == 1 and hasattr(node.contents[0], "contents"):
        clean_node(node.contents[0])
        return
    for child in node.contents:
        if any([isinstance(child, type) for type in (CData, Comment, Declaration, Doctype, ProcessingInstruction)]):
            child.decompose()
            continue
        if isinstance(child, Tag) and any([
            "betterdocs-hierarchial-toc" in gc.attrs.get("class", "")
            for gc in child.contents
            if isinstance(gc, Tag)
        ]):
            child.decompose()
            continue
        clean_node(child)
    for attr in list(node.attrs):
        if attr not in ["id", "class"]:
            del node[attr]
        if attr == "class" and "betterdocs-breadcrumb-item" not in node[attr]:
            del node[attr]
    return


def get_nested_questions(content) -> List[Mapping[str, str]]:
    qa_list = []
    nested = re.findall(r"\s*<p>\s*Q:\s*(.*?)\s*</p>\s*(<p>\s*A:\s*.*?\s*</p>\s*(?:<p>\s*.*?\s*</p>\s*)*?)(?:<hr[^>]*>)?", str(content), flags=re.DOTALL | re.MULTILINE)
    for question, content in nested:
        clean_content = re.sub(r"^<p>A: (.*?)</p>(.*)", r"<p>\1</p>\2", content.strip())
        qa_list.append({
            "question": question,
            "answer": BeautifulSoup(f"<div>{clean_content}</div>", "lxml").div,
        })
    return qa_list


def format_faq_item(
    title: Tag,
    content: Tag,
    category: Optional[str] = None,
    topic: Optional[str] = None,
    comments: Optional[str] = None,
) -> str:
    template = template_env().get_template("faq/page.html")
    return template.render(
        question=title.text.strip(),
        answer=content.prettify(formatter="html5"),
        qa_list=get_nested_questions(content),
        topic=topic,
        category=category,
        comments=comments,
    )


def get_tags_from_crumbs(crumbs: List[Tag]) -> Tuple[str, str]:
    topic, category = None, None
    while not topic or not category and len(crumbs):
        crumb = crumbs.pop()
        if not "item-current" in crumb.attrs.get("class", []):
            if not category:
                category = crumb.text.strip()
            elif not topic:
                topic = crumb.text.strip()
    return topic, category


def scrape_question(file_path: Path) -> str:
    with open(file_path, "r") as file:
        logger.info(f"  - {clean_path(file_path)}")
        html = file.read()
    soup = BeautifulSoup(html, "lxml")
    title = soup.find(id="betterdocs-entry-title")
    content = soup.find(id="betterdocs-single-content")
    crumbs = soup.findAll(class_="betterdocs-breadcrumb-item")
    topic, category = get_tags_from_crumbs(crumbs)
    cpath = file_path / "feed/index.html"
    comments = scrape_comments(cpath) if os.path.isfile(cpath / "index.html") else ""
    return format_faq_item(title, content, category=category, topic=topic, comments=comments)


def scrape_comments(file_path: Path) -> str:
    return ""


def scrape_all(dir: Path) -> Mapping[str, str]:
    faq = {}
    if not dir.is_dir():
        logger.warning(f"Directory not found: {clean_path(dir)}\n{dir}")
        return faq

    logger.info(dir)
    for qdir in os.listdir(dir):
        if qdir in ("feed", "index.html", "faq.html"):
            logger.warning(f"[SKIP: not an FAQ] {clean_path(dir / qdir)}")
            continue

        qpath = dir / qdir / "index.html"
        if not os.path.isfile(qpath):
            logger.warning(f"[SKIP: file not found] {clean_path(qpath)}")
            continue

        article = scrape_question(qpath).strip()
        if article:
            faq[qdir] = article
    return faq


def parse_args(timestamp: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=_script_file, description="BetterDocs FAQ scraper")

    parser.add_argument(
        "-d", "--domain",
        action="store",
        required=True,
        help="Domain name of site containing BetterDocs FAQ content",
    )
    parser.add_argument(
        "-p", "--path",
        action="store",
        required=True,
        help="Relative path to main FAQ page",
    )
    parser.add_argument(
        "-o", "--output-dir",
        action="store",
        default=f"{timestamp}-faq",
        help="Output directory to write scraped FAQ content to as separate HTML files",
    )
    parser.add_argument(
        "--log-level",
        action="store",
        default="WARN",
        choices=["INFO", "WARNING", "DEBUG"],
    )

    return parser.parse_args(sys.argv[1:])


def _retrieve_content():
    subprocess.run([
        "wget",
        "--https-only",
        "--tries=1",
        f"--output-file={_cwd / args.output_dir / 'wget.log'}",
        f"--rejected-log={_cwd / args.output_dir / 'wget.error.log' }",
        "-nc",
        "-c",
        "--show-progress",
        "-E",
        "--compression=auto",
        "--max-redirect=1",
        f'--accept-regex=^(https://{args.domain})?/{args.path}/*',
        f"--domains={args.domain}",
        "--recursive",
        "--no-parent",
        f"https://{args.domain}/{args.path}",
    ])


if __name__ == "__main__":
    require_user_consent(_base_dir.parent)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    args = parse_args(ts)
    args.path = args.path.strip("/")
    os.makedirs(_cwd / args.output_dir)
    logger.setLevel(getattr(logging, args.log_level))
    logger.addHandler(logging.FileHandler(filename=_cwd / args.output_dir / f"{args.log_level}.log"))
    logger.addHandler(logging.StreamHandler(stream=sys.stdout))
    _retrieve_content()
    faq = scrape_all(_cwd / args.domain / args.path)
    if not faq:
        print(f"No FAQ found for {args.domain}/{args.path}")
        exit(1)
    for id, qa in faq.items():
        with open(_cwd / args.output_dir / f"{id}.html", "w") as outfile:
            outfile.write(BeautifulSoup(qa).prettify(formatter="html5"))
    print(f"{len(faq)} FAQ from {args.domain}/{args.path} stored to {_cwd / args.output_dir}")
