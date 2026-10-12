"""Validate local plugin metadata without contacting the hosted MCP."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifests = [json.loads((ROOT / name).read_text()) for name in
             ('plugin.json', '.cursor-plugin/plugin.json', '.grok-plugin/plugin.json')]
for manifest in manifests:
    assert manifest['name'] == 'brew'
    assert manifest['version'] == manifests[0]['version']
    assert manifest['repository'] == 'https://github.com/GetBrew/brew-mcp'
    assert manifest['license'] == 'MIT'
    if 'logo' in manifest:
        assert (ROOT / manifest['logo']).is_file()
for path in ROOT.rglob('*.json'):
    if '.git' in path.parts:
        continue
    json.loads(path.read_text())
for path in [ROOT / 'mcp.json', *ROOT.rglob('*.mcp.json')]:
    config = json.loads(path.read_text())
    assert config['mcpServers']['brew']['url'] == 'https://brew.new/api/mcp', path
assert (ROOT / 'skills/brew/SKILL.md').is_file()
print('Plugin manifests and MCP configurations are valid.')

parser = argparse.ArgumentParser()
parser.add_argument('--catalog', type=Path)
args = parser.parse_args()
if args.catalog:
    tools = set(re.findall(r'^\| `([^`]+)` \|', args.catalog.read_text(), re.M))
    assert tools, 'Empty tool catalog'
    mentions = set(re.findall(r'`((?:get|list|create|edit|send|save|test|search)_[a-z_]+)`', (ROOT / 'skills/brew/SKILL.md').read_text()))
    assert mentions <= tools, f'Unknown skill tools: {sorted(mentions - tools)}'
    print('Skill tool names match the published catalog.')
