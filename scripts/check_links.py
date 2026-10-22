#!/usr/bin/env python3
"""只用标准库检查文献、相对链接、结构与机械风格；不写 cache/fixture。

退出码：0 全部通过，2 内容失败，3 网络未完成（若同时失败，2 优先）。
--self-test 不联网且不写文件；--lint 只运行本地检查。
"""
import argparse
from collections import Counter
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
    "README.md", "TASK-RECORD.md", "docs/01-problem-structure.md",
    "docs/02-method-landscape.md", "docs/03-retargeting-to-policy.md",
    "docs/04-genpo-interface.md", "docs/05-ppo-enhancement.md",
    "docs/bibliography.md", "scripts/check_links.py",
}
FIELDS = ("paper-id", "title", "authors-year", "arxiv", "tier", "evidence",
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
        if entry.get("tier") not in ("core", "extended"):
            errors.append(f"{pid}: tier 无效")
        coverage = entry.get("验证到哪里及缺口", "")
        coverage_match = re.fullmatch(r"已覆盖证据：(.*?)不支持的结论：(.*)", coverage)
        if not coverage_match or not all(part.strip() for part in coverage_match.groups()):
            errors.append(f"{pid}: 验证字段必须显式包含非空的已覆盖证据/不支持的结论")
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


def seed_manifest(text):
    seed = {}
    tier = None
    for line in text.splitlines():
        if line.startswith("### 3.1 "):
            tier = "core"
        elif line.startswith("### 3.2 "):
            tier = "extended"
        elif line.startswith("### 3.3 "):
            break
        m = re.match(r"- ([a-z0-9-]+) \| (\d{4}\.\d{4,5}v\d+) \|", line)
        if m and tier:
            seed[m[1]] = (m[2], tier)
    return seed


def entry_budget(entries, seed):
    errors = []
    actual = {e.get("paper-id"): e for e in entries}
    for pid, (version, tier) in seed.items():
        if pid not in actual:
            errors.append("缺少冻结条目: " + pid)
        elif (actual[pid].get("arxiv"), actual[pid].get("tier")) != (version, tier):
            errors.append("冻结身份/版本/tier 改变: " + pid)
    additions = set(actual) - set(seed)
    if len(entries) > 40 or len(additions) > 3:
        errors.append("文献预算超限")
    return errors, len(additions)


def reading_paths(text, ids):
    errors, sizes = [], []
    for heading in ("同事 A 路径", "Retargeting 路径"):
        m = re.search(r"^## " + heading + r"\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        refs = re.findall(r"docs/bibliography\.md#([a-z0-9-]+)", m[1]) if m else []
        sizes.append(len(refs))
        if not 5 <= len(refs) <= 7 or len(set(refs)) != len(refs):
            errors.append(f"阅读路径 {heading}: 须有 5–7 个不同 paper ID")
        if set(refs) - ids:
            errors.append(f"阅读路径 {heading}: 未知 paper ID")
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

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            self.meta[attrs.get("name")] = attrs.get("content", "")
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "name" in attrs:
            self.ids.add(attrs["name"])


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
            wait = max(0, 1.05 - (self.clock() - self.last.get(host, -1000)))
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
                    body = response.read().decode("utf-8", errors="strict")
                self.cache[url] = body
                return body
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
                    if retry_after.isdigit() and attempt < 2:
                        delay = float(retry_after)
                        if self.clock() + delay >= self.deadline:
                            raise NetworkIncomplete("Retry-After 超出总预算") from exc
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
        if name != "TASK-RECORD.md":
            errors.extend(f"{name}: {e}" for e in style_errors(texts[name]))
            counts = Counter(anchors(texts[name]))
            errors.extend(f"{name}: 重复 anchor {a}" for a, n in counts.items() if n > 1)
    entries, issues = parse_entries(texts.get("docs/bibliography.md", ""))
    errors.extend(issues)
    seed = seed_manifest(texts.get("TASK-RECORD.md", ""))
    if len(seed) != 37:
        errors.append("冻结清单无法解析为 37 条")
    issues, additions = entry_budget(entries, seed)
    errors.extend(issues)
    issues, sizes = reading_paths(texts.get("README.md", ""), {e.get("paper-id") for e in entries})
    errors.extend(issues)
    internal = 0
    external = set()
    for source, text in texts.items():
        for url in links(text):
            if url.startswith(("https://", "http://")):
                if source == "docs/bibliography.md":
                    external.add(url)
                continue
            internal += 1
            issue = relative_link(source, url, texts)
            if issue:
                errors.append(source + ": " + issue)
    tiers = Counter(e.get("tier") for e in entries)
    print(f"STRUCTURE: expected=9 actual={len(actual)} {'PASS' if actual == FILES else 'FAIL'}")
    print(f"STYLE: utf8_files={len([n for n in texts if n != 'TASK-RECORD.md'])} (UTF-8 strict; fence-aware tables; banned terms)")
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
            body = fetch.get(base)
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
                elif not (parsed.hostname == "doi.org" or page.meta.get("citation_doi")):
                    issue = "非 arXiv 链接须是 DOI/publisher 主源（缺 citation_doi）"
                if fragment and urllib.parse.unquote(fragment) not in page.ids:
                    issue = "外部死 anchor: " + fragment
            if issue:
                raise ContentFailure(issue + ": " + url)
            verified += 1
            print("VERIFIED " + url, flush=True)
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

    good = "## sample-2024\n" + "\n".join("- " + k + "：" + v for k, v in zip(FIELDS, (
        "sample-2024", "A Test Title", "Doe 等 2024", "2401.12345v2", "core", "v2 abstract",
        "问题", "方法", "已覆盖证据：已测范围。 不支持的结论：未测迁移。", "用途")))
    entries, errors = parse_entries(good)
    check(not errors, "valid entry")
    check(bool(parse_entries(good.replace("2401.12345v2", "wrong-id"))[1]), "wrong ID")
    check(bool(parse_entries(good.replace("- title：A Test Title", ""))[1]), "missing field")
    check(bool(parse_entries(good + "\n" + good)[1]), "duplicate paper ID and anchor")
    duplicate = good.replace("sample-2024", "second-2024").replace("2401.12345v2", "2401.12345v3")
    check(any("重复作品" in e for e in parse_entries(good + "\n" + duplicate)[1]), "duplicate canonical work across versions")
    check(bool(parse_entries(good.replace("tier：core", "tier：other"))[1]), "invalid tier")
    check(bool(parse_entries(good.replace("解决什么问题", "问题是什么"))[1]), "exact four-question schema")
    check(bool(parse_entries(good.replace("不支持的结论：未测迁移。", ""))[1]), "explicit unsupported conclusions required")
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
    check(bool(style_errors(BANNED[0])), "banned term detected without echo")
    check(normalize_title("Title: A-B") == normalize_title("TITLE A B"), "title punctuation/case normalization")
    check(bool(reading_paths("## 同事 A 路径\n", {"sample-2024"})[0]), "missing/short reading paths")
    check(bool(entry_budget(entries * 41, {})[0]), "total and addition budgets")
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
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"OK"

    now, calls = [0.0], []

    def redirect_opener(request, timeout):
        calls.append(now[0])
        if request.full_url.endswith("/old"):
            raise urllib.error.HTTPError(request.full_url, 302, "mock", {"Location": "/new"}, None)
        return Response()

    client = Fetcher(opener=redirect_opener, clock=lambda: now[0], sleep=lambda n: now.__setitem__(0, now[0] + n), alarms=False)
    check(client.get("https://example.invalid/old") == "OK" and calls[1] - calls[0] >= 1, "redirect respects per-host interval")
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
