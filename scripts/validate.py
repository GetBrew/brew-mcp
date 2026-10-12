#!/usr/bin/env python3
"""Validate the Brew MCP plugin repository. Standard library only.

Checks, in order:
  1. every JSON file parses
  2. every plugin manifest: name, repository, license, logo and icon files
  3. every plugin manifest carries the same version, matching CHANGELOG.md
     (and the tag, with --tag)
  4. every MCP config points at the one canonical MCP endpoint, with no headers
  5. server.json is a valid, publishable MCP Registry entry (it versions
     separately from the plugin manifests, see check_server_json)
  6. the Claude Code marketplace lists the plugin
  7. skills, rules and referenced assets exist and their frontmatter is valid
  8. voice: no "ESP", no em or en dashes, no removed image-generation tools
  9. with --catalog FILE: every tool the skill, rule and README text names
     exists in the published tool catalog (docs.brew.new/api-reference/mcp/tools.md)

Usage: python3 scripts/validate.py [--tag v1.2.3] [--catalog tools.md]
"""

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_URL = "https://brew.new/api/mcp"
REPO_URL = "https://github.com/GetBrew/brew-mcp"
ICON_PREFIX = "https://brew.new/logo/"
SKIP_DIRS = {".git", "node_modules"}

# Plugin manifests whose "version" must move together. server.json is not in
# this list: the MCP Registry version follows MCP_SERVER_JSON_VERSION in
# brew-v2 (lib/mcp/server-json.ts), which the website serves at
# /.well-known/mcp/server.json, and the registry refuses a version it already
# has. It moves when the served file changes, not on every plugin release.
VERSIONED = [
    ".claude-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".grok-plugin/plugin.json",
    "plugin.json",
    "gemini-extension.json",
]

# The manifests that describe the plugin itself also name the repository and
# the license. gemini-extension.json carries neither.
PLUGIN_MANIFESTS = VERSIONED[:4]

# Guided workflows are MCP prompts, not tools. Several start with a verb a tool
# also uses (set_up_automation), so the catalog check skips them.
GUIDED_WORKFLOWS = {
    "launch_email_campaign",
    "build_segment_and_send",
    "set_up_automation",
    "wire_trigger_from_code",
    "analyze_campaign_performance",
    "personalize_with_crm",
    "improve_deliverability",
    "configure_brand",
    "run_audience_automation",
    "onboard_brand",
    "report_mcp_issue",
}

# Real tools the docs table does not list (organization connections only).
EXTRA_TOOLS = {"create_brand"}

# Text the catalog check reads for tool names.
CATALOG_FILES = ["README.md", "GEMINI.md", "llms-install.md"]

# Text files the voice check reads. This script is excluded on purpose: its
# patterns spell out the characters it forbids.
VOICE_SUFFIXES = (".md", ".mdc", ".json", ".yaml", ".yml", ".txt")
EM_DASH = "—"
EN_DASH = "–"
VOICE_RULES = [
    (re.compile(r"\bESP\b"), 'the word "ESP" (say "email platform")'),
    (re.compile(r"email service provider", re.I), '"email service provider"'),
    (re.compile(EM_DASH), "an em dash"),
    (re.compile(EN_DASH), "an en dash"),
    (
        re.compile(r"\b(generate_image|create_gif|transform_image)\b"),
        "a removed image-generation tool",
    ),
]

SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")

errors = []


def fail(message):
    errors.append(message)


def rel(path):
    return os.path.relpath(path, ROOT)


def walk_files():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            yield os.path.join(base, name)


def load_json(relpath):
    path = os.path.join(ROOT, relpath)
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        fail(f"{relpath}: file is missing")
    except json.JSONDecodeError as error:
        fail(f"{relpath}: invalid JSON ({error})")
    return None


def check_json_syntax():
    count = 0
    for path in walk_files():
        if path.endswith(".json"):
            count += 1
            try:
                with open(path, encoding="utf-8") as handle:
                    json.load(handle)
            except json.JSONDecodeError as error:
                fail(f"{rel(path)}: invalid JSON ({error})")
    print(f"json: {count} files parsed")


def check_manifests():
    for relpath in VERSIONED:
        data = load_json(relpath)
        if data is None:
            continue
        if data.get("name") != "brew":
            fail(f'{relpath}: name must be "brew"')
        if relpath in PLUGIN_MANIFESTS:
            if data.get("repository") != REPO_URL:
                fail(f"{relpath}: repository must be {REPO_URL}")
            if data.get("license") != "MIT":
                fail(f'{relpath}: license must be "MIT"')
        for field in ("logo", "icon"):
            if field in data and not os.path.isfile(
                os.path.join(ROOT, os.path.normpath(data[field]))
            ):
                fail(f"{relpath}: {field} {data[field]!r} is not a file in this repository")
    print(f"manifests: {len(VERSIONED)} plugin manifests are named and complete")


def check_versions(tag):
    versions = {}
    for relpath in VERSIONED:
        data = load_json(relpath)
        if data is None:
            continue
        version = data.get("version")
        if not isinstance(version, str) or not SEMVER.match(version):
            fail(f"{relpath}: version {version!r} is not semver")
            continue
        versions[relpath] = version
    distinct = set(versions.values())
    if len(distinct) > 1:
        detail = ", ".join(f"{p}={v}" for p, v in sorted(versions.items()))
        fail(f"versions differ: {detail}")
    elif distinct:
        version = next(iter(distinct))
        changelog = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read()
        heading = re.search(r"^## (\d+\.\d+\.\d+\S*)", changelog, re.M)
        if not heading or heading.group(1) != version:
            fail(
                f"CHANGELOG.md: newest heading is "
                f"{heading.group(1) if heading else 'missing'}, expected {version}"
            )
        if tag is not None and tag != f"v{version}":
            fail(f"tag {tag} does not match manifest version {version}")
        print(f"versions: all {len(versions)} manifests at {version}")


def servers_of(data, key="mcpServers"):
    servers = (data or {}).get(key)
    if not isinstance(servers, dict) or set(servers) != {"brew"}:
        return None
    return servers["brew"]


def check_endpoints():
    configs = [
        (".mcp.json", "url"),
        ("mcp.json", "url"),
        ("gemini-extension.json", "httpUrl"),
    ]
    known = {relpath for relpath, _ in configs}
    configs += [
        (rel(path), "url")
        for path in sorted(walk_files())
        if path.endswith(".mcp.json") and rel(path) not in known
    ]
    for relpath, field in configs:
        entry = servers_of(load_json(relpath))
        if entry is None:
            fail(f'{relpath}: mcpServers must hold exactly one server named "brew"')
            continue
        if entry.get(field) != MCP_URL:
            fail(f"{relpath}: {field} must be {MCP_URL}")
        if "headers" in entry or "env" in entry:
            fail(f"{relpath}: the remote server uses OAuth, so no headers or env")
    docker = open(
        os.path.join(ROOT, "directories/docker/server.yaml"), encoding="utf-8"
    ).read()
    if f"url: {MCP_URL}" not in docker:
        fail(f"directories/docker/server.yaml: url must be {MCP_URL}")
    print("endpoints: every manifest points at the canonical URL with no headers")


def check_server_json():
    data = load_json("server.json")
    if data is None:
        return
    expected = {
        "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
        "name": "new.brew/mcp",
        "websiteUrl": "https://brew.new/mcp",
    }
    for key, value in expected.items():
        if data.get(key) != value:
            fail(f"server.json: {key} must be {value!r}")
    description = data.get("description", "")
    if not description or len(description) > 100:
        fail(f"server.json: description must be 1 to 100 characters ({len(description)})")
    if not data.get("title"):
        fail("server.json: title is required")
    repository = data.get("repository") or {}
    if repository.get("url") != REPO_URL or repository.get("source") != "github":
        fail(f"server.json: repository must be {REPO_URL} (source github)")
    remotes = data.get("remotes")
    if (
        not isinstance(remotes, list)
        or len(remotes) != 1
        or remotes[0].get("type") != "streamable-http"
        or remotes[0].get("url") != MCP_URL
        or "headers" in remotes[0]
    ):
        fail(f"server.json: remotes must be one streamable-http entry at {MCP_URL} with no headers")
    if "packages" in data:
        fail("server.json: this is a remote-only server, so no packages")
    version = data.get("version")
    if not isinstance(version, str) or not SEMVER.match(version):
        fail(f"server.json: version {version!r} is not semver")
    # Same icons brew-v2 serves: PNG first (clients must render PNG and JPEG;
    # SVG is optional), then the light and dark SVG marks.
    icons = data.get("icons")
    if not isinstance(icons, list) or not icons:
        fail("server.json: icons are required (the registry shows them in listings)")
    else:
        for icon in icons:
            if not str(icon.get("src", "")).startswith(ICON_PREFIX):
                fail(f"server.json: icon {icon.get('src')!r} must be served from {ICON_PREFIX}")
            if not icon.get("mimeType"):
                fail(f"server.json: icon {icon.get('src')!r} needs a mimeType")
        if icons[0].get("mimeType") != "image/png":
            fail("server.json: the first icon must be a PNG")
    print(f"server.json: registry entry {version} is sane")


def check_claude_marketplace():
    plugin = load_json(".claude-plugin/plugin.json") or {}
    market = load_json(".claude-plugin/marketplace.json") or {}
    if market.get("name") != "brew-mcp":
        fail('.claude-plugin/marketplace.json: name must be "brew-mcp" (install id brew@brew-mcp)')
    entries = market.get("plugins") or []
    if [e.get("name") for e in entries] != [plugin.get("name")]:
        fail("marketplace.json plugin entry name must match .claude-plugin/plugin.json")
    for entry in entries:
        if entry.get("source") != "./":
            fail('marketplace.json: the plugin lives at the repo root, so source must be "./"')


def read_frontmatter(path):
    """The YAML between the leading --- lines, or None."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    return text[4:end] if end != -1 else None


def check_frontmatter_scalars(relpath, front):
    """A plain YAML scalar cannot hold ": " (a nested mapping) or " #" (a comment)."""
    for line in front.splitlines():
        match = re.match(r"^[A-Za-z_-]+:\s*(\S.*)$", line)
        if not match:
            continue
        value = match.group(1)
        if value[0] in "\"'[{|>&*!":
            continue
        if ": " in value or " #" in value:
            fail(f"{relpath}: quote this frontmatter value, it contains ': ' or ' #': {line.strip()[:60]}")


def check_files():
    skills = os.path.join(ROOT, "skills")
    names = sorted(os.listdir(skills)) if os.path.isdir(skills) else []
    if not names:
        fail("skills/: at least one skill is required")
    for name in names:
        path = os.path.join(skills, name, "SKILL.md")
        if not os.path.isfile(path):
            fail(f"skills/{name}: SKILL.md is missing")
            continue
        front = read_frontmatter(path) or ""
        match = re.search(r"^name:\s*(\S+)\s*$", front, re.M)
        if not match or match.group(1) != name:
            fail(f"skills/{name}/SKILL.md: frontmatter name must be {name!r}")
        if not re.search(r"^description:\s*\S", front, re.M):
            fail(f"skills/{name}/SKILL.md: frontmatter description is required")
        check_frontmatter_scalars(f"skills/{name}/SKILL.md", front)
    rules = os.path.join(ROOT, "rules")
    for name in sorted(os.listdir(rules)) if os.path.isdir(rules) else []:
        if not name.endswith(".mdc"):
            continue
        front = read_frontmatter(os.path.join(rules, name))
        if front is None or not re.search(r"^description:\s*\S", front, re.M):
            fail(f"rules/{name}: frontmatter with a description is required")
            continue
        check_frontmatter_scalars(f"rules/{name}", front)
    for relpath in [
        "assets/logo.svg",
        "assets/icon-400.png",
        "assets/icon-512.png",
        "rules/brew.mdc",
        "GEMINI.md",
        "llms-install.md",
        "LICENSE",
    ]:
        if not os.path.isfile(os.path.join(ROOT, relpath)):
            fail(f"{relpath}: file is missing")
    # Docker's CONTRIBUTING: a remote server always ships `[]` here; its tools
    # come from the live server (`dynamic: tools: true` in server.yaml).
    if load_json("directories/docker/tools.json") != []:
        fail("directories/docker/tools.json: a remote server's tools.json must be []")
    print(f"files: {len(names)} skill(s), rules and assets present")


def check_voice():
    scanned = 0
    for path in walk_files():
        if not path.endswith(VOICE_SUFFIXES):
            continue
        scanned += 1
        with open(path, encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                for pattern, label in VOICE_RULES:
                    if pattern.search(line):
                        fail(f"{rel(path)}:{number}: found {label}")
    print(f"voice: {scanned} text files checked")


def check_catalog(catalog):
    """Every tool the shipped text names must exist in the published catalog."""
    with open(catalog, encoding="utf-8") as handle:
        tools = set(re.findall(r"^\| `([^`]+)` \|", handle.read(), re.M))
    if not tools:
        fail(f"{catalog}: no tools found in the catalog")
        return
    tools |= EXTRA_TOOLS
    # A tool name is verb_noun. The verbs are the ones the catalog itself uses,
    # so ids such as brand_id or idempotency_key are never mistaken for tools.
    # "control" catches the retired control_email_send and control_audience_run.
    verbs = {name.split("_")[0] for name in tools if "_" in name} | {"control"}
    pattern = re.compile(r"`((?:%s)(?:_[a-z]+)+)`" % "|".join(sorted(verbs)))
    paths = [os.path.join(ROOT, name) for name in CATALOG_FILES]
    for folder, suffix in (("skills", ".md"), ("rules", ".mdc")):
        for base, _dirs, files in os.walk(os.path.join(ROOT, folder)):
            paths += [os.path.join(base, f) for f in files if f.endswith(suffix)]
    checked = 0
    for path in sorted(paths):
        if not os.path.isfile(path):
            continue
        checked += 1
        with open(path, encoding="utf-8") as handle:
            mentioned = set(pattern.findall(handle.read()))
        unknown = sorted(mentioned - tools - GUIDED_WORKFLOWS)
        if unknown:
            fail(f"{rel(path)}: tools missing from the published catalog: {', '.join(unknown)}")
    print(f"catalog: tool names in {checked} files match the {len(tools)} published tools")


def main():
    parser = argparse.ArgumentParser(description="Validate the Brew MCP plugin repository.")
    parser.add_argument("--tag", help="release tag (v1.2.3) the manifests must match")
    parser.add_argument("--catalog", help="published MCP tool catalog (tools.md) to check tool names against")
    args = parser.parse_args()
    check_json_syntax()
    check_manifests()
    check_versions(args.tag)
    check_endpoints()
    check_server_json()
    check_claude_marketplace()
    check_files()
    check_voice()
    if args.catalog:
        check_catalog(args.catalog)
    if errors:
        print(f"\n{len(errors)} problem(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
