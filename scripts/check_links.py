#!/usr/bin/env python3
"""只用标准库检查文献、相对链接、结构与机械风格；不写 cache/fixture。

退出码：0 全部通过，2 内容失败，3 网络未完成（若同时失败，2 优先）。
--self-test 不联网且不写文件；--lint 只运行本地检查。
"""
import argparse
from collections import Counter, namedtuple
import html
import http.client
from html.parser import HTMLParser
from pathlib import Path
import re
import signal
import socket
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "README.md", "docs/01-problem-structure.md",
    "docs/02-method-landscape.md", "docs/03-retargeting-to-policy.md",
    "docs/04-onpolicy-diffusion-interface.md", "docs/05-ppo-enhancement.md",
    "docs/bibliography.md", "docs/06-diffusion-history.md",
    "docs/regrind-integration.md", "scripts/check_links.py",
}
EXPECTED_FILES = len(FILES)
# CO-1 批准身份：稳定 paper ID -> 所据版本、tier；标题/年份勘误不改变身份。
# 书目不再冻结：FROZEN_WORKS 仅作原 36 篇身份锚定，允许新增条目，总量不设硬上限。
FROZEN_WORKS = {
    "openai-inhand-2020": ("1808.00177v5", "core"),
    "openai-rubiks-2019": ("1910.07113v1", "core"),
    "dextreme-2022": ("2210.13702v2", "core"),
    "visual-dexterity-2022": ("2211.11744v3", "core"),
    "sequential-dexterity-2023": ("2309.00987v2", "core"),
    "dapg-2018": ("1709.10087v2", "core"),
    "bi-dexhands-2023": ("2206.08686v2", "core"),
    "isaac-lab-2023": ("2301.04195v2", "core"),
    "dexpilot-2020": ("1910.03135v2", "core"),
    "anyteleop-2023": ("2307.04577v3", "core"),
    "dexcap-2024": ("2403.07788v2", "core"),
    "diffusion-policy-2023": ("2303.04137v5", "core"),
    "dppo-2024": ("2409.00588v3", "core"),
    "ppo-2017": ("1707.06347v2", "core"),
    "implementation-matters-2020": ("2005.12729v1", "core"),
    "massively-parallel-2021": ("2109.11978v3", "core"),
    "residual-rl-2018": ("1812.03201v2", "core"),
    "sapg-2024": ("2407.20230v1", "core"),
    "demostart-2024": ("2409.06613v2", "core"),
    "leap-hand-2023": ("2309.06440v1", "extended"),
    "zhu-2018": ("1810.06045v1", "extended"),
    "trifinger-2021": ("2108.09779v2", "extended"),
    "rotate-touch-2023": ("2303.10880v4", "extended"),
    "openteach-2024": ("2403.07870v1", "extended"),
    "bunny-visionpro-2024": ("2407.03162v1", "extended"),
    "robotic-telekinesis-2022": ("2202.10448v2", "extended"),
    "mimicplay-2023": ("2302.12422v2", "extended"),
    "dexmimicgen-2024": ("2410.24185v2", "extended"),
    "dp3-2024": ("2403.03954v7", "extended"),
    "dexdiffuser-2023": ("2402.02989v3", "extended"),
    "diffusion-ql-2022": ("2208.06193v3", "extended"),
    "idql-2023": ("2304.10573v2", "extended"),
    "on-policy-actor-critic-2020": ("2006.05990v1", "extended"),
    "domain-randomization-2017": ("1703.06907v1", "extended"),
    "mappo-2021": ("2103.01955v4", "extended"),
    "deepmimic-2018": ("1804.02717v3", "extended"),
}
READING_HEADINGS = ()
ROUTE_HEADING = "起步路线"
ROUTE_MIN_REFS = 1
ROUTE_MAX_REFS = 4
OFFICIAL_HOST = "isaac-sim.github.io"
OFFICIAL_PATH = "/IsaacLab/v2.2.0/source/overview/environments.html"
OFFICIAL_TITLE = "Available Environments — Isaac Lab Documentation"
OFFICIAL_ANCHORS = {
    "manipulation": ("Isaac-Repose-Cube-Shadow-Direct-v0", "Isaac-Lift-Cube-Franka-v0"),
    "classic": ("Isaac-Ant-v0",),
}
FetchResult = namedtuple("FetchResult", "body final_url status")
FIELDS = ("paper-id", "title", "authors-year", "arxiv", "tier", "evidence", "主源",
          "解决什么问题", "方法与信号是什么", "验证到哪里及缺口", "对两类读者有什么用")
ARXIV = re.compile(r"\d{4}\.\d{4,5}v[1-9]\d*")
QUESTIONS = FIELDS[-4:]
BANNED = ("冒" + "烟" + "测" + "试", "实" + "锤")
ATOM = {"a": "http://www.w3.org/2005/Atom"}


def normalize_title(text):
    text = unicodedata.normalize("NFKC", html.unescape(text)).casefold()
    return "".join(c for c in text if c.isalnum())


def container_line(line):
    """剥离 blockquote/list 容器标记，供容器内的 fence 与表格识别。"""
    while True:
        stripped = re.sub(r"^\s*(?:>\s?|[-+*]\s+|\d+[.)]\s+)", "", line, count=1)
        if stripped == line:
            return line
        line = stripped


def prose_lines(text):
    """保留行号，屏蔽 fenced code（同字符、至少同长度的关闭 fence）。"""
    fence = None
    result = []
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", container_line(line))
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= fence[1] and not match[2].strip():
                fence = None
            result.append("")
        elif match and not (match[1][0] == "`" and "`" in match[2]):
            fence = (match[1][0], len(match[1]))
            result.append("")
        else:
            result.append(line)
    return result


def cells(line):
    # GFM 表格中的转义竖线不分列，code span 内的未转义竖线仍分列。
    parts, start, slashes = [], 0, 0
    line = container_line(line).strip()
    for i, char in enumerate(line):
        if char == "|" and slashes % 2 == 0:
            parts.append(line[start:i])
            start = i + 1
        slashes = slashes + 1 if char == "\\" else 0
    parts.append(line[start:])
    if parts and not parts[0].strip():
        parts.pop(0)
    if parts and not parts[-1].strip():
        parts.pop()
    return [part.strip() for part in parts]


def table_lines(text):
    lines = prose_lines(text)
    found = []
    for i in range(1, len(lines)):
        row = cells(lines[i])
        # 无外侧竖线的多列表格和有外侧竖线的单列表格均识别。
        if row and "|" in lines[i] + lines[i - 1] and all(re.fullmatch(r":?-+:?", c) for c in row):
            header = cells(lines[i - 1])
            if len(header) == len(row) and any(header):
                found.append(i + 1)
    return found


def style_errors(text):
    errors = [f"markdown table delimiter at line {n}" for n in table_lines(text)]
    for word in BANNED:
        if word in text:
            errors.append("禁止词命中（不回显词项）")
    return errors


def anchors(text):
    result = []
    for line in prose_lines(text):
        match = re.match(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", line)
        if match:
            label = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", match[1])
            label = re.sub(r"<[^>]+>", "", label).replace("`", "")
            label = re.sub(r"[^\w\-\s]", "", label.lower())
            result.append(re.sub(r"\s", "-", label))
        result.extend(re.findall(r'<a\s+(?:id|name)=[\"\']([^\"\']+)[\"\']', line))
    return result


def links(text):
    """解析本仓库使用的 inline、reference、autolink 与 HTML href/src。"""
    clean = "\n".join(prose_lines(text))
    definitions = dict(re.findall(r"^\s*\[([^\]]+)\]:\s*<?([^\s>]+)>?", clean, re.M))
    found = re.findall(r"!?\[[^\]\n]*\]\(\s*<?([^\s)>]+)>?(?:\s+\"[^\"]*\")?\s*\)", clean)
    for label, ref in re.findall(r"\[([^\]\n]+)\]\[([^\]\n]*)\]", clean):
        found.append(definitions.get(ref or label, "INVALID_REFERENCE:" + (ref or label)))
    found.extend(definitions.values())
    found.extend(re.findall(r"<(https?://[^>]+)>", clean))
    found.extend(re.findall(r'(?:href|src)=[\"\']([^\"\']+)[\"\']', clean))
    return found


def parse_entries(text):
    entries, errors = [], []
    chunks = re.split(r"^## ([a-z0-9][a-z0-9-]+)\s*$", text, flags=re.M)
    for i in range(1, len(chunks), 2):
        pid, body = chunks[i:i + 2]
        entry = {"anchor": pid}
        for key in FIELDS:
            values = re.findall(r"^- " + re.escape(key) + r"[：:]\s*(.*?)\s*$", body, re.M)
            if len(values) != 1 or not values[0].strip():
                errors.append(f"{pid}: 字段 {key} 缺失、重复或为空")
            else:
                entry[key] = values[0]
        if entry.get("paper-id") != pid:
            errors.append(f"{pid}: paper-id 与 heading anchor 不符")
        if not ARXIV.fullmatch(entry.get("arxiv", "")):
            errors.append(f"{pid}: arxiv 必须含合法 canonical ID 与 vN")
        sources = links(entry.get("主源", ""))
        if not sources:
            errors.append(f"{pid}: 主源必须包含绑定所据 arxiv ID/version 的链接")
        for source in sources:
            parsed = urllib.parse.urlsplit(source)
            if (parsed.scheme not in ("http", "https") or parsed.netloc != "arxiv.org"
                    or parsed.path not in ("/abs/" + entry.get("arxiv", ""),
                                           "/html/" + entry.get("arxiv", "")) or parsed.query):
                errors.append(f"{pid}: 主源链接与所据 arxiv ID/version 不符: {source}")
        if entry.get("tier") not in ("core", "extended"):
            errors.append(f"{pid}: tier 无效")
        coverage = entry.get("验证到哪里及缺口", "")
        coverage_match = re.fullmatch(r"已覆盖证据：(.*?)后续核查：(.*)", coverage)
        if not coverage_match or not all(part.strip() for part in coverage_match.groups()):
            errors.append(f"{pid}: 验证字段必须显式包含非空的已覆盖证据/后续核查")
        version = entry.get("arxiv", "").split("v")[-1]
        evidence = entry.get("evidence", "")
        if not re.search(r"\bv" + re.escape(version) + r"\b", evidence):
            errors.append(f"{pid}: evidence 缺少所据版本")
        if not re.search(r"abstract|Section|Eq\.|Appendix", evidence):
            errors.append(f"{pid}: evidence 缺少 abstract 或 section/equation 定位")
        entries.append(entry)
    if not entries:
        errors.append("bibliography 没有条目")
    for key in ("paper-id", "anchor"):
        for value, count in Counter(e.get(key) for e in entries).items():
            if count > 1:
                errors.append(f"重复 {key}: {value}")
    works = [e.get("arxiv", "").split("v")[0] for e in entries]
    if len(works) != len(set(works)):
        errors.append("重复作品（忽略版本）")
    return entries, errors


def entry_budget(entries, seed=FROZEN_WORKS):
    errors = []
    actual = {e.get("paper-id"): e for e in entries}
    for pid, (version, tier) in seed.items():
        if pid not in actual:
            errors.append("缺少锚定条目: " + pid)
        elif (actual[pid].get("arxiv"), actual[pid].get("tier")) != (version, tier):
            errors.append("锚定身份/版本/tier 改变: " + pid)
    additions = set(actual) - set(seed)
    tiers = Counter(e.get("tier") for e in entries)
    return errors, len(additions)


def reading_paths(text, ids):
    """起步路线块：每条 ### 路线引 1–4 个已知 paper ID，无重复。"""
    errors, sizes = [], []
    m = re.search(r"^## " + ROUTE_HEADING + r"\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return [f"缺少 {ROUTE_HEADING} 章节"], sizes
    routes = re.split(r"^### ", m[1], flags=re.M)[1:]
    if not routes:
        return [f"{ROUTE_HEADING} 下没有 ### 路线块"], sizes
    for route in routes:
        title = route.splitlines()[0].strip()
        refs = re.findall(r"docs/bibliography\.md#([a-z0-9-]+)", route)
        sizes.append(len(refs))
        if not ROUTE_MIN_REFS <= len(refs) <= ROUTE_MAX_REFS or len(set(refs)) != len(refs):
            errors.append(f"路线 {title}: 须有 {ROUTE_MIN_REFS}–{ROUTE_MAX_REFS} 个不同 paper ID")
        if set(refs) - ids:
            errors.append(f"路线 {title}: 未知 paper ID")
    return errors, sizes


def relative_link(source, url, texts, root=ROOT):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme or parsed.netloc:
        return "不支持的相对链接: " + url
    path = urllib.parse.unquote(parsed.path)
    target = (root / source).parent / path if path else root / source
    resolved = target.resolve()
    if not resolved.is_relative_to(root.resolve()):
        return "越界路径: " + url
    name = str(resolved.relative_to(root.resolve()))
    if name not in texts and name not in FILES:
        return "不存在的目标: " + url
    if parsed.fragment and (name not in texts or urllib.parse.unquote(parsed.fragment) not in anchors(texts[name])):
        return "死 anchor: " + url
    return None


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.ids = set()
        self.title_parts = []
        self.title_count = 0
        self.in_title = False
        self.text_parts = []
        self.elements = []
        self.fragments = {}
        self.headings = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        element = {"tag": tag, "start": len(self.text_parts),
                   "heading_start": len(self.headings), "heading_end": None}
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append((len(self.text_parts), int(tag[1])))
        if tag in ("area", "base", "br", "col", "embed", "hr", "img", "input",
                   "link", "meta", "param", "source", "track", "wbr"):
            element["heading_end"] = len(self.headings)
        else:
            self.elements.append(element)
        if tag == "title":
            self.in_title = True
            self.title_count += 1
        if tag == "meta":
            self.meta[attrs.get("name")] = attrs.get("content", "")
        if "id" in attrs:
            self.ids.add(attrs["id"])
            self.fragments[attrs["id"]] = element
        if tag == "a" and "name" in attrs:
            self.ids.add(attrs["name"])
            self.fragments[attrs["name"]] = element

    def handle_endtag(self, tag):
        for i in range(len(self.elements) - 1, -1, -1):
            if self.elements[i]["tag"] == tag:
                for element in self.elements[i:]:
                    element["heading_end"] = len(self.headings)
                del self.elements[i:]
                break
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        self.text_parts.append(data)
        if self.in_title:
            self.title_parts.append(data)

    def section_text(self, fragment):
        """从 fragment 元素起，截到下一同级/更高 heading；保留下级内容。"""
        element = self.fragments[fragment]
        first = element["heading_start"]
        last = element["heading_end"]
        if last is None:
            last = len(self.headings)
        # section/div 的首个内含 heading 定级；其他元素沿用前一 heading。
        heading = first if first < last else first - 1
        level = self.headings[heading][1] if heading >= 0 else 6
        end = next((start for start, rank in self.headings[heading + 1:] if rank <= level),
                   len(self.text_parts))
        return " ".join(self.text_parts[element["start"]:end])

    @property
    def title(self):
        return " ".join("".join(self.title_parts).split())


def official_url_issue(url, require_fragment=True):
    """官方工程文档白名单同时约束 host、固定版本 path 与 fragment。"""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("http", "https") or parsed.netloc != OFFICIAL_HOST:
        return "官方工程文档 hostname/scheme 不符"
    if parsed.path != OFFICIAL_PATH or parsed.query:
        return "官方工程文档固定版本/path 不符"
    fragment = urllib.parse.unquote(parsed.fragment)
    if (require_fragment or fragment) and fragment not in OFFICIAL_ANCHORS:
        return "官方工程文档 fragment 未绑定"
    return None


def official_page_issue(url, result):
    issue = official_url_issue(url) or official_url_issue(result.final_url, require_fragment=False)
    if issue:
        return issue
    if result.status != 200:
        return "官方工程文档最终 status 非 200"
    fragment = urllib.parse.unquote(urllib.parse.urlsplit(url).fragment)
    final_fragment = urllib.parse.unquote(urllib.parse.urlsplit(result.final_url).fragment)
    if final_fragment and final_fragment != fragment:
        return "官方工程文档 redirect 改变 fragment"
    page = Page()
    page.feed(result.body)
    if page.title_count != 1 or page.title != OFFICIAL_TITLE:
        return "官方工程文档 page title 不符"
    if fragment not in page.ids:
        return "官方工程文档死 anchor: " + fragment
    text = page.section_text(fragment)
    if any(pid not in text for pid in OFFICIAL_ANCHORS[fragment]):
        return "官方工程文档缺少绑定的 registry ID"
    return None


def api_metadata(body, entry):
    try:
        doc = ET.fromstring(body)
    except ET.ParseError:
        return "API 返回非 Atom XML"
    rows = doc.findall("a:entry", ATOM)
    if len(rows) != 1:
        return "API 条目数量不符"
    returned = (rows[0].findtext("a:id", "", ATOM)).rsplit("/", 1)[-1]
    title = rows[0].findtext("a:title", "", ATOM)
    if returned != entry["arxiv"]:
        return "API ID/version 不符: " + returned
    if normalize_title(title) != normalize_title(entry["title"]):
        return "API title 不符: " + title
    return None


class ContentFailure(Exception):
    pass


class NetworkIncomplete(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        # Redirect 也经 Fetcher，避免绕过同 host 请求间隔和预算。
        return None


class Fetcher:
    def __init__(self, opener=None, clock=time.monotonic, sleep=time.sleep, alarms=True):
        self.opener = opener or urllib.request.build_opener(NoRedirect).open
        self.clock, self.sleep, self.alarms = clock, sleep, alarms
        self.deadline = clock() + 900
        self.last = {}
        self.cache = {}

    def get(self, url, redirects=0):
        if redirects > 5:
            raise ContentFailure("过多 redirects: " + url)
        if url in self.cache:
            return self.cache[url]
        host = urllib.parse.urlsplit(url).netloc
        reason = ""
        for attempt in range(3):
            remaining = self.deadline - self.clock()
            if remaining <= 0:
                raise NetworkIncomplete("总运行上限 15 分钟")
            interval = 3.05 if host == "export.arxiv.org" else 1.05
            wait = max(0, interval - (self.clock() - self.last.get(host, -1000)))
            if wait >= remaining:
                raise NetworkIncomplete("总运行上限 15 分钟")
            self.sleep(wait)
            self.last[host] = self.clock()
            timeout = min(15, self.deadline - self.clock())
            old = None
            retry_delay = 0.0
            redirect_url = None
            if self.alarms and hasattr(signal, "setitimer"):
                old = signal.signal(signal.SIGALRM, self._timeout)
                signal.setitimer(signal.ITIMER_REAL, timeout)
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "dex-onboarding-link-check/1.0"})
                with self.opener(request, timeout=timeout) as response:
                    status = response.status
                    final_url = response.geturl()
                    body = response.read().decode("utf-8", errors="strict")
                if status != 200:
                    raise ContentFailure(f"最终 HTTP {status}: {final_url}")
                result = FetchResult(body, final_url, status)
                self.cache[url] = result
                return result
            except urllib.error.HTTPError as exc:
                if exc.code in (301, 302, 303, 307, 308) and exc.headers.get("Location"):
                    redirect_url = urllib.parse.urljoin(url, exc.headers["Location"])
                    if urllib.parse.urlsplit(redirect_url).scheme not in ("http", "https"):
                        raise ContentFailure("非 HTTP redirect: " + redirect_url) from exc
                else:
                    if exc.code not in (408, 425, 429) and not 500 <= exc.code <= 599:
                        raise ContentFailure(f"HTTP {exc.code}: {url}") from exc
                    reason = f"HTTP {exc.code}"
                    retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                    if attempt < 2:
                        delay = max(5.0 * (2 ** attempt), float(retry_after) if retry_after.isdigit() else 0.0)
                        if self.clock() + delay >= self.deadline:
                            raise NetworkIncomplete("重试等待超出总预算") from exc
                        retry_delay = delay
            except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError, OSError, http.client.HTTPException) as exc:
                reason = type(exc).__name__
            except UnicodeError as exc:
                raise ContentFailure("返回内容不是 UTF-8: " + url) from exc
            finally:
                if old is not None:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    signal.signal(signal.SIGALRM, old)
            if redirect_url:
                self.cache[url] = self.get(redirect_url, redirects + 1)
                return self.cache[url]
            self.sleep(retry_delay)
        raise NetworkIncomplete(f"{reason}，3 次尝试后仍未完成: {url}")

    @staticmethod
    def _timeout(signum, frame):
        raise TimeoutError("单请求超过时限")


def exit_code(failed, unverified):
    return 2 if failed else (3 if unverified else 0)


def local_checks():
    errors, texts = [], {}
    actual = set()
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if relative.parts[0] == ".git":
            continue
        if path.is_symlink():
            errors.append("不允许 symlink: " + str(relative))
        if path.is_file() or path.is_symlink():
            actual.add(str(relative))
        elif path.is_dir() and str(relative) not in ("docs", "scripts"):
            errors.append("额外目录: " + str(relative))
    if actual != FILES:
        errors.append(f"结构不符: missing={sorted(FILES - actual)} extra={sorted(actual - FILES)}")
    for name in sorted(FILES):
        if not name.endswith(".md"):
            continue
        try:
            texts[name] = (ROOT / name).read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{name}: {exc}")
            continue
        errors.extend(f"{name}: {e}" for e in style_errors(texts[name]))
        counts = Counter(anchors(texts[name]))
        errors.extend(f"{name}: 重复 anchor {a}" for a, n in counts.items() if n > 1)
    entries, issues = parse_entries(texts.get("docs/bibliography.md", ""))
    errors.extend(issues)
    issues, additions = entry_budget(entries)
    errors.extend(issues)
    issues, sizes = reading_paths(texts.get("README.md", ""), {e.get("paper-id") for e in entries})
    errors.extend(issues)
    internal = 0
    external = set()
    for source, text in texts.items():
        for url in links(text):
            if url.startswith(("https://", "http://")):
                external.add(url)
                parsed = urllib.parse.urlsplit(url)
                if parsed.hostname not in ("arxiv.org", "export.arxiv.org", "doi.org"):
                    issue = official_url_issue(url)
                    if issue:
                        errors.append(source + ": " + issue + ": " + url)
                continue
            internal += 1
            issue = relative_link(source, url, texts)
            if issue:
                errors.append(source + ": " + issue)
    tiers = Counter(e.get("tier") for e in entries)
    print(f"STRUCTURE: expected={EXPECTED_FILES} actual={len(actual)} {'PASS' if actual == FILES else 'FAIL'}")
    print(f"STYLE: utf8_files={len(texts)} (UTF-8 strict; fence-aware tables; banned terms)")
    candidates = [(name, n, line) for name, text in sorted(texts.items())
                  for n, line in enumerate(text.splitlines(), 1) if "门" in line]
    print(f"METAPHOR-CANDIDATES: {len(candidates)} (仅列候选，人工裁决)")
    for name, n, line in candidates:
        print(f"CANDIDATE {name}:{n}: {line}")
    print(f"OFFICIAL-SOURCES: {sum(official_url_issue(u) is None for u in external)} (全部交付 Markdown)")
    print(f"LINT: entries={len(entries)} core={tiers['core']} extended={tiers['extended']} additions={additions} paths={'/'.join(map(str, sizes))} internal_links={internal}")
    return entries, errors, external, internal


def full_check(entries, external, internal):
    fetch = Fetcher()
    verified, failed, unverified = internal, 0, 0
    index = {e["arxiv"]: e for e in entries}
    jobs = [("api", "https://export.arxiv.org/api/query?id_list=" + e["arxiv"], e) for e in entries]
    jobs.extend(("link", url, None) for url in sorted(external))
    for kind, url, entry in jobs:
        try:
            base, fragment = urllib.parse.urldefrag(url)
            result = fetch.get(base)
            body = result.body
            issue = None
            if kind == "api":
                issue = api_metadata(body, entry)
            else:
                page = Page()
                page.feed(body)
                parsed = urllib.parse.urlsplit(base)
                if parsed.hostname in ("arxiv.org", "export.arxiv.org"):
                    match = re.fullmatch(r"/(abs|html)/(\d{4}\.\d{4,5}v\d+)", parsed.path)
                    if not match or match[2] not in index:
                        issue = "arXiv 链接未绑定已记录版本"
                    elif match[1] == "abs":
                        expected = index[match[2]]
                        if page.meta.get("citation_arxiv_id") != expected["arxiv"].split("v")[0]:
                            issue = "abs ID 元数据不符"
                        elif normalize_title(page.meta.get("citation_title", "")) != normalize_title(expected["title"]):
                            issue = "abs title 元数据不符"
                    elif normalize_title(index[match[2]]["title"]) not in normalize_title(body):
                        issue = "HTML title 不符"
                elif parsed.hostname == "doi.org":
                    if not page.meta.get("citation_doi"):
                        issue = "DOI 最终页缺 citation_doi"
                else:
                    issue = official_page_issue(url, result)
                if fragment and urllib.parse.unquote(fragment) not in page.ids:
                    issue = "外部死 anchor: " + fragment
            if issue:
                raise ContentFailure(issue + ": " + url)
            verified += 1
            print(f"VERIFIED {url} [status={result.status} final={result.final_url}]", flush=True)
        except ContentFailure as exc:
            failed += 1
            print("FAILED " + str(exc), flush=True)
        except NetworkIncomplete as exc:
            unverified += 1
            print("UNVERIFIED " + str(exc), flush=True)
    print(f"verified={verified} failed={failed} unverified={unverified}")
    return exit_code(failed, unverified)


def self_test():
    checks = 0

    def check(condition, label):
        nonlocal checks
        if not condition:
            raise AssertionError(label)
        checks += 1
        print("SELF-TEST PASS " + label)

    source = "[arXiv v2](https://arxiv.org/abs/2401.12345v2)"
    good = "## sample-2024\n" + "\n".join("- " + k + "：" + v for k, v in zip(FIELDS, (
        "sample-2024", "A Test Title", "Doe 等 2024", "2401.12345v2", "core", "v2 abstract", source,
        "问题", "方法", "已覆盖证据：已测范围。 后续核查：未测迁移。", "用途")))
    entries, errors = parse_entries(good)
    check(not errors, "valid entry")
    check(bool(parse_entries(good.replace("- 主源：" + source + "\n", ""))[1]), "missing primary source")
    check(bool(parse_entries(good + "\n- 主源：" + source)[1]), "duplicate primary source")
    for label, replacement in (
        ("blank primary source", ""),
        ("primary source without URL", "arXiv v2"),
        ("primary source version mismatch", source.replace("12345v2", "12345v3")),
        ("primary source ID mismatch", source.replace("12345v2", "54321v2")),
        ("unversioned primary source", source.replace("12345v2", "12345")),
    ):
        check(bool(parse_entries(good.replace(source, replacement))[1]), label)
    sections = "[§3](https://arxiv.org/html/2401.12345v2#S3)、[§4](https://arxiv.org/html/2401.12345v2#S4)"
    check(not parse_entries(good.replace(source, sections + "、" + source))[1],
          "multiple HTML sections and abs bind the same version")
    check(bool(parse_entries(good.replace(source, sections + "、" + source.replace("12345v2", "12345v3")))[1]),
          "mixed primary source versions rejected")
    check(bool(parse_entries(good.replace("2401.12345v2", "wrong-id"))[1]), "wrong ID")
    check(bool(parse_entries(good.replace("- title：A Test Title", ""))[1]), "missing field")
    check(bool(parse_entries(good + "\n" + good)[1]), "duplicate paper ID and anchor")
    duplicate = good.replace("sample-2024", "second-2024").replace("2401.12345v2", "2401.12345v3")
    check(any("重复作品" in e for e in parse_entries(good + "\n" + duplicate)[1]), "duplicate canonical work across versions")
    check(bool(parse_entries(good.replace("tier：core", "tier：other"))[1]), "invalid tier")
    check(bool(parse_entries(good.replace("解决什么问题", "问题是什么"))[1]), "exact four-question schema")
    check(bool(parse_entries(good.replace("后续核查：未测迁移。", ""))[1]), "explicit unsupported conclusions required")
    check(bool(parse_entries(good.replace("已覆盖证据：已测范围。", "已覆盖证据：   "))[1]), "blank evidence coverage rejected")
    check(bool(parse_entries(good.replace("v2 abstract", "v20 abstract"))[1]), "evidence version boundary")
    atom = '<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://arxiv.org/abs/2401.12345v2</id><title>A Test Title</title></entry></feed>'
    check(api_metadata(atom, entries[0]) is None, "valid API metadata")
    check(api_metadata(atom.replace("A Test Title", "Other Title"), entries[0]) is not None, "title mismatch despite HTTP 200")
    check(api_metadata(atom.replace("12345v2", "54321v2"), entries[0]) is not None, "ID mismatch despite HTTP 200")
    check(api_metadata(atom.replace("v2", "v3"), entries[0]) is not None, "wrong comparison version")
    check(api_metadata("<html>OK</html>", entries[0]) is not None, "200 without metadata")
    texts = {"README.md": "# 存在的标题\n"}
    check(relative_link("README.md", "#存在的标题", texts) is None, "valid Unicode heading")
    check(relative_link("README.md", "#missing", texts) is not None, "dead anchor")
    check(relative_link("README.md", "../escape.md", texts) is not None, "path escape")
    check(relative_link("README.md", "%2e%2e/escape.md", texts) is not None, "encoded path escape")
    check(bool(table_lines("A | B\n--- | :---:\n1 | 2")), "table without outer pipes")
    check(bool(table_lines("| A |\n| --- |\n| 1 |")), "one-column table")
    check(not table_lines("````md\n```\nA | B\n--- | ---\n````"), "nested shorter fence does not close")
    check(not table_lines("~~~\nA | B\n--- | ---\n~~~"), "tilde fence")
    check(not table_lines("x\n---\na\\|b"), "not a table")
    check(bool(table_lines("> A | B\n> --- | ---")), "blockquote table")
    check(bool(table_lines("- A | B\n  --- | ---")), "list-container table")
    check(not table_lines("> ```\n> A | B\n> --- | ---\n> ```"), "blockquote code fence")
    check(cells("A" + chr(92) + "|B | C") == ["A" + chr(92) + "|B", "C"], "escaped table pipe")
    check(cells("A" + chr(92) * 2 + "|B | C") == ["A" + chr(92) * 2, "B", "C"], "even backslashes before table pipe")
    check(bool(table_lines("A | B\n--- | ---")) and not table_lines("```md\nA | B\n--- | ---\n```"),
          "fence-aware style checks apply to authorized prose")
    check(bool(style_errors(BANNED[0])), "banned term detected without echo")
    check(normalize_title("Title: A-B") == normalize_title("TITLE A B"), "title punctuation/case normalization")
    check(bool(reading_paths("## " + ROUTE_HEADING + "\n", {"sample-2024"})[0]), "missing/short route paths")
    frozen = [{"paper-id": pid, "arxiv": version, "tier": tier}
              for pid, (version, tier) in FROZEN_WORKS.items()]
    check(entry_budget(frozen) == ([], 0), "approved 36 identities and 19/17 tiers")
    check(any("缺少锚定条目" in e for e in entry_budget(frozen[1:])[0]), "deleted frozen ID")
    replaced = [dict(e) for e in frozen]
    replaced[0]["paper-id"] = "replacement-2024"
    check(any("缺少锚定条目" in e for e in entry_budget(replaced)[0]), "replaced frozen ID")
    for key, value in (("arxiv", "1808.00177v6"), ("tier", "extended")):
        changed = [dict(e) for e in frozen]
        changed[0][key] = value
        check(any("身份/版本/tier" in e for e in entry_budget(changed)[0]), "frozen " + key + " tamper")
    check(entry_budget(frozen + entries) == ([], 1), "additions now allowed beyond frozen 36")
    reading = "## " + ROUTE_HEADING + "\n" + "\n".join(
        "### 路线 " + str(i) + "\n1. [p](docs/bibliography.md#" + e["paper-id"] + ")"
        for i, e in enumerate(frozen[:3], 1))
    ids = {e["paper-id"] for e in frozen}
    check(reading_paths(reading, ids) == ([], [1, 1, 1]), "new route headings and valid paths")
    check(bool(reading_paths(reading.replace(frozen[0]["paper-id"], "unknown-id"), ids)[0]), "unknown route-path ID")
    for code in ("timeout", 429, 503):
        calls = []
        now = [0.0]

        def opener(request, timeout):
            calls.append(now[0])
            if code == "timeout":
                raise TimeoutError()
            raise urllib.error.HTTPError(request.full_url, code, "mock", {}, None)

        client = Fetcher(opener=opener, clock=lambda: now[0], sleep=lambda n: now.__setitem__(0, now[0] + n), alarms=False)
        try:
            client.get("https://example.invalid/x")
            outcome = False
        except NetworkIncomplete:
            outcome = True
        check(outcome and len(calls) == 3 and all(b - a >= 1 for a, b in zip(calls, calls[1:])), f"{code}: 2 retries, rate limit, unverified")
        if code != "timeout":
            check(calls[1] - calls[0] >= 5 and calls[2] - calls[1] >= 10, f"{code}: bounded retry backoff")
    class Response:
        status = 200

        def __init__(self, url, body="OK"):
            self.url, self.body = url, body

        def geturl(self):
            return self.url

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return self.body.encode("utf-8")

    now, calls = [0.0], []

    def redirect_opener(request, timeout):
        calls.append(now[0])
        if request.full_url.endswith("/old"):
            raise urllib.error.HTTPError(request.full_url, 302, "mock", {"Location": "/new"}, None)
        return Response(request.full_url)

    client = Fetcher(opener=redirect_opener, clock=lambda: now[0], sleep=lambda n: now.__setitem__(0, now[0] + n), alarms=False)
    fetched = client.get("https://example.invalid/old")
    check(fetched == FetchResult("OK", "https://example.invalid/new", 200) and calls[1] - calls[0] >= 1,
          "redirect preserves final URL/status and per-host interval")
    now[0] = 901
    try:
        client.get("https://example.invalid/uncached")
        bounded = False
    except NetworkIncomplete:
        bounded = True
    check(bounded, "900-second total budget")

    def missing_opener(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 404, "mock", {}, None)

    try:
        Fetcher(opener=missing_opener, alarms=False).get("https://example.invalid/missing")
        missing = False
    except ContentFailure:
        missing = True
    check(missing, "404 is content failure")

    official_base = "https://" + OFFICIAL_HOST + OFFICIAL_PATH
    official_url = official_base + "#manipulation"
    official_body = ("<html><title>" + html.escape(OFFICIAL_TITLE) + "</title>"
                     '<section id="manipulation">' + " ".join(OFFICIAL_ANCHORS["manipulation"]) + "</section></html>")
    valid = FetchResult(official_body, official_base, 200)
    check(official_page_issue(official_url, valid) is None, "valid fixed-version official page")
    registry = " ".join(OFFICIAL_ANCHORS["manipulation"])
    section_prefix = "<html><title>" + html.escape(OFFICIAL_TITLE) + "</title>"
    for label, section, expected in (
        ("registry IDs before fragment rejected",
         "<h2>Other</h2>" + registry + '<h2 id="manipulation">Manipulation</h2><p>Empty</p>', False),
        ("registry IDs after same-level heading rejected",
         '<section id="manipulation"><h2>Manipulation</h2><p>Empty</p></section>'
         "<section><h2>Other</h2>" + registry + "</section>", False),
        ("registry IDs after higher-level heading rejected",
         '<h3 id="manipulation">Manipulation</h3><p>Empty</p><h2>Other</h2>' + registry, False),
        ("fragment heading includes lower-level subsection",
         '<h2 id="manipulation">Manipulation</h2><h3>Tasks</h3>' + registry + "<h2>Other</h2>", True),
        ("fragment container includes lower-level subsection",
         '<section id="manipulation"><h2>Manipulation</h2><h3>Tasks</h3>' + registry + "</section>", True),
        ("fragment inside heading uses its level",
         '<h2><span id="manipulation">Manipulation</span></h2><h3>Tasks</h3>' + registry, True),
        ("fragment inside heading stops at its peer",
         '<h2><span id="manipulation">Manipulation</span></h2><h2>Other</h2>' + registry, False),
    ):
        result = valid._replace(body=section_prefix + section + "</html>")
        check((official_page_issue(official_url, result) is None) == expected, label)
    for label, result in (
        ("200 wrong official title", valid._replace(body=official_body.replace("Available Environments", "Not Found"))),
        ("wrong official version", valid._replace(final_url=official_base.replace("v2.2.0", "main"))),
        ("non-official host", valid._replace(final_url=official_base.replace(OFFICIAL_HOST, "example.invalid"))),
        ("dead official anchor", valid._replace(body=official_body.replace('id="manipulation"', 'id="other"'))),
        ("missing registry ID", valid._replace(body=official_body.replace(OFFICIAL_ANCHORS["manipulation"][0], "other"))),
        ("non-200 final status", valid._replace(status=204)),
        ("redirect changes fragment", valid._replace(final_url=official_base + "#classic")),
    ):
        check(official_page_issue(official_url, result) is not None, label)
    check(official_page_issue(official_url.replace(OFFICIAL_HOST, "example.invalid"), valid) is not None,
          "non-official requested host")
    check(official_page_issue(official_url.replace("v2.2.0", "latest"), valid) is not None,
          "unversioned requested path")
    check(official_page_issue(official_base + "#dead", valid) is not None, "unbound requested fragment")
    for label, target, expected in (
        ("legal official HTTP-to-HTTPS redirect", official_base, True),
        ("redirect to non-official host rejected", official_base.replace(OFFICIAL_HOST, "example.invalid"), False),
        ("redirect to wrong version rejected", official_base.replace("v2.2.0", "v2.1.0"), False),
    ):
        now = [0.0]
        requested = official_base.replace("https://", "http://")

        def official_redirect(request, timeout):
            if request.full_url == requested:
                raise urllib.error.HTTPError(request.full_url, 301, "mock", {"Location": target}, None)
            return Response(request.full_url, official_body)

        client = Fetcher(opener=official_redirect, clock=lambda: now[0],
                         sleep=lambda n: now.__setitem__(0, now[0] + n), alarms=False)
        result = client.get(requested)
        check((official_page_issue(requested + "#manipulation", result) is None) == expected, label)
    check(exit_code(0, 1) == 3 and exit_code(1, 1) == 2 and exit_code(0, 0) == 0, "three exit classes")
    print(f"SELF-TEST: {checks} passed, 0 failed; no network/files written")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--lint", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    entries, errors, external, internal = local_checks()
    for error in errors:
        print("FAILED " + error)
    if errors:
        print(f"verified=0 failed={len(errors)} unverified=0")
        return 2
    print("LOCAL: PASS (structure, schema, reading paths, internal links, style)")
    if args.lint:
        print(f"verified={internal + len(entries)} failed=0 unverified=0 (local only)")
        return 0
    return full_check(entries, external, internal)


if __name__ == "__main__":
    raise SystemExit(main())
