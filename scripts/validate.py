#!/usr/bin/env python3
"""Validate the Brew MCP plugin repository. Standard library only.

Checks, in order:
  1. every JSON file parses
  2. every manifest carries the same version (and the tag, with --tag)
  3. every manifest points at the one canonical MCP endpoint, with no headers
  4. server.json is a valid, publishable MCP Registry entry
  5. skills and referenced assets exist
  6. voice: no "ESP", no em or en dashes, no removed image-generation tools

Usage: python3 scripts/validate.py [--tag v1.2.3]
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_URL = "https://brew.new/api/mcp"
REPO_URL = "https://github.com/GetBrew/brew-mcp"
SKIP_DIRS = {".git", "node_modules"}

# Manifests whose "version" must move together.
VERSIONED = [
    ".claude-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".grok-plugin/plugin.json",
    "plugin.json",
    "gemini-extension.json",
    "server.json",
]

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
    print("server.json: registry entry is sane")


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
        head = open(path, encoding="utf-8").read().split("---")
        front = head[1] if len(head) > 2 else ""
        match = re.search(r"^name:\s*(\S+)\s*$", front, re.M)
        if not match or match.group(1) != name:
            fail(f"skills/{name}/SKILL.md: frontmatter name must be {name!r}")
        if not re.search(r"^description:\s*\S", front, re.M):
            fail(f"skills/{name}/SKILL.md: frontmatter description is required")
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
    tools = load_json("directories/docker/tools.json") or []
    seen = set()
    for tool in tools:
        name = tool.get("name")
        if not name or not tool.get("description"):
            fail(f"directories/docker/tools.json: every tool needs a name and a description ({tool})")
        if name in seen:
            fail(f"directories/docker/tools.json: duplicate tool {name}")
        seen.add(name)
    print(f"files: {len(names)} skill(s), assets and {len(tools)} docker tools present")


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


def main():
    tag = None
    if "--tag" in sys.argv:
        tag = sys.argv[sys.argv.index("--tag") + 1]
    check_json_syntax()
    check_versions(tag)
    check_endpoints()
    check_server_json()
    check_claude_marketplace()
    check_files()
    check_voice()
    if errors:
        print(f"\n{len(errors)} problem(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
