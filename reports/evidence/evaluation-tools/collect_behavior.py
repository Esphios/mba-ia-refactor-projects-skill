"""Collect post-evaluation hashes; equality is structural evidence, not model scoring."""
import hashlib, json, pathlib, sys

root = pathlib.Path(sys.argv[1])
repo = pathlib.Path(__file__).resolve().parents[3]

def manifest(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob('*')) if p.is_file()}

before = json.loads((root / 'preparation.json').read_text())
extension = root / 'extension-before.json'
if extension.exists():
    before['before'].update(json.loads(extension.read_text()))
after = {name:manifest(root / name) for name in before['before']}
comparison = {}
for name, old in before['before'].items():
    new = after[name]
    comparison[name] = {'unchanged': old == new,
        'changed_files': [p for p in sorted(set(old) | set(new)) if old.get(p) != new.get(p)]}
source_now = manifest(repo / 'code-smells-project/.agents/skills/refactor-arch')
output = dict(before, after=after, comparison=comparison,
              canonical_skill_unchanged=source_now == before['skill_source_manifest'])
target = root / 'observed-run.json'
target.write_text(json.dumps(output, indent=2))
print(json.dumps({'comparison':comparison, 'canonical_skill_unchanged':output['canonical_skill_unchanged'],
                  'output':str(target)}))
