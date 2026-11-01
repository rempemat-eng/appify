"""Read-only checks for the formats consumed by Quests and Dialogue.

Events, flags and restore IDs remain open to world scripts. Reachability is an
overapproximation of normal notify() progression from fresh quest state, not a
playthrough or a closed registry of every possible world event.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import sys
from typing import Any

from .conditions import has_uncovered_state, possible


@dataclass(frozen=True, order=True)
class Finding:
    file: str
    path: str
    code: str
    message: str

    def __str__(self) -> str:
        return f'{self.file}:{self.path}: {self.code}: {self.message}'


class _Object(dict):
    """Preserve duplicate-key evidence instead of silently accepting last wins."""
    def __init__(self, pairs):
        super().__init__()
        self.duplicates = []
        for key, value in pairs:
            if key in self:
                self.duplicates.append(key)
            self[key] = value


def _child(path: str, key: str) -> str:
    return f'{path}[{json.dumps(key, ensure_ascii=True)}]'


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _integer(value: Any) -> bool:
    # Godot JSON numbers pass through float64 before int64 conversion. Reject
    # values whose rounding/overflow could change thresholds or branch order.
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and -2**63 <= value < 2**63 and math.isfinite(value)
            and int(value) == value and int(float(value)) == value)


class _Validator:
    def __init__(self, root: Path):
        self.root = root
        self.findings: list[Finding] = []
        self.quests: dict[str, tuple[str, dict]] = {}
        self.speakers: dict[str, list[tuple[str, str, dict]]] = {}
        self.conditions: list[tuple[str, str, dict | None]] = []
        self.events: list[tuple[str, str, str]] = []
        self.quest_count = self.dialogue_count = 0

    def fault(self, file: str, path: str, code: str, message: str):
        self.findings.append(Finding(file, path, code, message))

    def duplicates(self, value: Any, file: str, path='$'):
        if isinstance(value, _Object):
            for key in value.duplicates:
                self.fault(file, _child(path, key), 'json.duplicate',
                           f'duplicate object key {key!r}; the runtime would overwrite it')
        if isinstance(value, dict):
            for key, child in value.items():
                self.duplicates(child, file, _child(path, key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self.duplicates(child, file, f'{path}[{index}]')

    def documents(self, name: str):
        directory = self.root / 'data' / name
        if not directory.is_dir():
            self.fault(f'data/{name}', '$', 'io.directory', 'data directory does not exist')
            return
        try:
            files = sorted(path for path in directory.iterdir()
                           if path.is_file() and path.name.endswith('.json'))
        except OSError as error:
            self.fault(f'data/{name}', '$', 'io.directory', str(error))
            return
        for path in files:
            file = path.relative_to(self.root).as_posix()
            try:
                def nonfinite(token):
                    raise ValueError(f'non-finite JSON number {token}')
                value = json.loads(path.read_text(encoding='utf-8'),
                                   object_pairs_hook=_Object, parse_constant=nonfinite)
            except (OSError, UnicodeError, ValueError, RecursionError) as error:
                self.fault(file, '$', 'json.parse', str(error))
                continue
            try:
                self.duplicates(value, file)
            except RecursionError:
                self.fault(file, '$', 'json.depth', 'JSON nesting exceeds the validator depth limit')
                continue
            yield file, value

    def strings(self, value: Any, file: str, path: str) -> bool:
        if not isinstance(value, list) or any(not _text(item) for item in value):
            self.fault(file, path, 'schema.strings', 'expected an array of nonempty strings')
            return False
        return True

    def condition(self, value: Any, file: str, path: str):
        # null is the same unguarded branch used by check(step.get("if")).
        if value is None:
            self.conditions.append((file, path, value))
            return
        if not isinstance(value, dict):
            self.fault(file, path, 'condition.shape', 'expected a condition object or null')
            return
        arrays = {'flags', 'not_flags', 'done', 'active', 'not_started',
                  'restored', 'not_restored'}
        for key, field in value.items():
            location = _child(path, key)
            if key in arrays:
                self.strings(field, file, location)
            elif key == 'step':
                if not isinstance(field, list) or len(field) != 2 or any(not _text(x) for x in field):
                    self.fault(file, location, 'condition.step', 'expected [quest id, step id]')
            elif key == 'glint_at_least':
                if not _integer(field):
                    self.fault(file, location, 'condition.glint', 'expected an integer Glint threshold')
            else:
                self.fault(file, location, 'condition.operator',
                           f'unsupported condition operator {key!r}; Quests.check ignores it')
        self.conditions.append((file, path, value))

    def event(self, value: Any, file: str, path: str):
        if not _text(value):
            self.fault(file, path, 'schema.event', 'expected a nonempty event string')
        else:
            self.events.append((file, path, value))

    def quest(self, file: str, value: Any):
        self.quest_count += 1
        if not isinstance(value, dict):
            self.fault(file, '$', 'quest.shape', 'expected a quest object')
            return
        identifier = value.get('id')
        if not _text(identifier):
            self.fault(file, '$.id', 'quest.id', 'expected a nonempty quest id')
        elif identifier in self.quests:
            self.fault(file, '$.id', 'quest.duplicate', f'duplicate quest id {identifier!r}')
        else:
            self.quests[identifier] = (file, value)
        for key in ('title', 'kind', 'summary', 'region'):
            if key in value and not isinstance(value[key], str):
                self.fault(file, f'$.{key}', 'schema.text', 'expected a string')
        if 'start' in value:
            start = value['start']
            if not isinstance(start, dict):
                self.fault(file, '$.start', 'quest.start', 'expected a start object')
            else:
                if 'on' in start:
                    self.event(start['on'], file, '$.start.on')
                self.condition(start.get('if'), file, '$.start.if')
        steps = value.get('steps')
        if not isinstance(steps, list) or not steps:
            self.fault(file, '$.steps', 'quest.steps', 'expected a nonempty array of steps')
        else:
            ids = set()
            for index, step in enumerate(steps):
                path = f'$.steps[{index}]'
                if not isinstance(step, dict):
                    self.fault(file, path, 'quest.step', 'expected a step object')
                    continue
                sid = step.get('id')
                if not _text(sid):
                    self.fault(file, path + '.id', 'step.id', 'expected a nonempty step id')
                elif sid in ids:
                    self.fault(file, path + '.id', 'step.duplicate', f'duplicate step id {sid!r}')
                else:
                    ids.add(sid)
                if 'text' in step and not isinstance(step['text'], str):
                    self.fault(file, path + '.text', 'schema.text', 'expected a string')
                if 'on' in step:
                    self.event(step['on'], file, path + '.on')
                self.condition(step.get('if'), file, path + '.if')
                if 'done_if' in step:
                    self.condition(step['done_if'], file, path + '.done_if')
                if 'set_flags' in step:
                    self.strings(step['set_flags'], file, path + '.set_flags')
        if 'rewards' in value:
            rewards = value['rewards']
            if not isinstance(rewards, dict):
                self.fault(file, '$.rewards', 'quest.rewards', 'expected a rewards object')
            else:
                if 'glint' in rewards and not _integer(rewards['glint']):
                    self.fault(file, '$.rewards.glint', 'schema.integer', 'expected integer Glint')
                if 'flags' in rewards:
                    self.strings(rewards['flags'], file, '$.rewards.flags')

    def dialogue(self, file: str, value: Any):
        self.dialogue_count += 1
        if not isinstance(value, dict):
            self.fault(file, '$', 'dialogue.shape', 'expected an object keyed by speaker id')
            return
        for identifier, speaker in value.items():
            path = _child('$', identifier)
            if not _text(identifier) or not isinstance(speaker, dict):
                self.fault(file, path, 'dialogue.speaker', 'expected a named speaker object')
                continue
            self.speakers.setdefault(identifier, [])
            if 'name' in speaker and not isinstance(speaker['name'], str):
                self.fault(file, path + '.name', 'schema.text', 'expected a string')
            entries = speaker.get('entries', [])
            if not isinstance(entries, list):
                self.fault(file, path + '.entries', 'dialogue.entries', 'expected an array of entries')
                continue
            for index, entry in enumerate(entries):
                location = f'{path}.entries[{index}]'
                if not isinstance(entry, dict):
                    self.fault(file, location, 'dialogue.entry', 'expected an entry object')
                    continue
                if 'priority' in entry and (not _integer(entry['priority']) or entry['priority'] == -2**63):
                    self.fault(file, location + '.priority', 'dialogue.priority',
                               'expected an exact JSON integer whose negated sort key fits Godot int64')
                lines = entry.get('lines', [])
                if not isinstance(lines, list) or any(not isinstance(line, str) for line in lines):
                    self.fault(file, location + '.lines', 'dialogue.lines', 'expected an array of strings')
                self.condition(entry.get('if'), file, location + '.if')
                self.speakers[identifier].append((file, location, entry))

    def references(self):
        for file, path, event in self.events:
            if event.startswith('talk:') and event[5:] not in self.speakers:
                self.fault(file, path, 'reference.speaker', f'unknown dialogue speaker {event[5:]!r}')
        for file, path, cond in self.conditions:
            if not isinstance(cond, dict):
                continue
            for key in ('done', 'active', 'not_started'):
                values = cond.get(key, [])
                if not isinstance(values, list):
                    continue
                for index, identifier in enumerate(values):
                    if _text(identifier) and identifier not in self.quests:
                        self.fault(file, f'{_child(path, key)}[{index}]', 'reference.quest',
                                   f'unknown quest {identifier!r}')
            step = cond.get('step')
            if isinstance(step, list) and len(step) == 2 and all(_text(x) for x in step):
                identifier, sid = step
                if identifier not in self.quests:
                    self.fault(file, path + '.step', 'reference.quest', f'unknown quest {identifier!r}')
                else:
                    steps = self.quests[identifier][1].get('steps', [])
                    if isinstance(steps, list) and not any(isinstance(s, dict) and s.get('id') == sid for s in steps):
                        self.fault(file, path + '.step', 'reference.step',
                                   f'unknown step {sid!r} in quest {identifier!r}')

    def semantics(self):
        steps = {qid: [s['id'] for s in value['steps']] for qid, (_, value) in self.quests.items()}
        # Fresh normal progression, with open external events/flags/restorations.
        # The union deliberately permits states from different playthroughs: it
        # can miss a deadlock, but cannot manufacture one from unknown producers.
        reached = {qid: {'none'} for qid in self.quests}
        changed = True
        while changed:
            changed = False
            for qid, (_, quest) in self.quests.items():
                before = len(reached[qid])
                start = quest.get('start', {})
                # Public start_quest() also supports explicitly script-started
                # quests with no authored event entry. Do not invent a trigger.
                if not start.get('on') or possible(start.get('if'), steps, {**reached, qid: {'none'}}):
                    reached[qid].add('step:' + steps[qid][0])
                for step in quest['steps']:
                    state = 'step:' + step['id']
                    if state not in reached[qid]:
                        continue
                    context = {**reached, qid: {state}}
                    routes = []
                    if step.get('on'):
                        routes.append(step.get('if'))
                    if 'done_if' in step:
                        routes.append(step['done_if'])
                    if any(possible(cond, steps, context) for cond in routes):
                        index = steps[qid].index(step['id'])
                        reached[qid].add('step:' + steps[qid][index + 1] if index + 1 < len(steps[qid]) else 'done')
                changed |= before != len(reached[qid])
        for qid, (file, quest) in self.quests.items():
            if 'step:' + steps[qid][0] not in reached[qid]:
                self.fault(file, '$.start', 'quest.unreachable_start',
                           'no event-driven start route from fresh quest state; check prerequisite cycles or self-state guards')
                continue
            for index, step in enumerate(quest['steps']):
                state = 'step:' + step['id']
                if state not in reached[qid]:
                    self.fault(file, f'$.steps[{index}]', 'quest.unreachable_step',
                               f'step {step["id"]!r} cannot be reached after preceding steps')
                    continue
                context = {**reached, qid: {state}}
                routes = ([step.get('if')] if step.get('on') else [])
                if 'done_if' in step:
                    routes.append(step['done_if'])
                if not any(possible(cond, steps, context) for cond in routes):
                    self.fault(file, f'$.steps[{index}]', 'quest.blocked_step',
                               f'step {step["id"]!r} has no possible event/if or done_if completion route')
        for entries in self.speakers.values():
            # Python's stable sort preserves the runtime's alphabetical-file /
            # original-entry tie order, including speakers extended across files.
            ordered = sorted(entries, key=lambda e: -e[2].get('priority', 0))
            prior = []
            for file, path, entry in ordered:
                cond = entry.get('if')
                if not possible(cond, steps):
                    self.fault(file, path + '.if', 'dialogue.impossible', 'condition cannot hold in any quest state')
                elif not has_uncovered_state(cond, prior, steps):
                    self.fault(file, path, 'dialogue.shadowed', 'earlier merged entries cover every matching state')
                prior.append(cond)

    def run(self):
        for file, value in self.documents('quests'):
            self.quest(file, value)
        for file, value in self.documents('dialogue'):
            self.dialogue(file, value)
        self.references()
        # Structural/reference errors must be fixed before the graph is sound.
        # Still read every file and report all independent structural problems.
        if not self.findings:
            self.semantics()
        return sorted(set(self.findings))


def validate(game_root: Path) -> list[Finding]:
    """Validate every immediate JSON file loaded by the existing two autoloads."""
    return _Validator(Path(game_root)).run()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2] / 'game',
                        help='Godot game root (contains data/quests and data/dialogue)')
    args = parser.parse_args(argv)
    validator = _Validator(args.root)
    findings = validator.run()
    for finding in findings:
        # Invalid Unicode in authored keys/filenames must still produce a
        # diagnostic, including when a CI console uses an ASCII encoding.
        encoding = sys.stdout.encoding or 'utf-8'
        print(str(finding).encode(encoding, errors='backslashreplace').decode(encoding))
    if findings:
        print(f'Quest/dialogue validation failed: {len(findings)} finding(s).')
        return 1
    print(f'Quest/dialogue validation passed: {validator.quest_count} quest files, '
          f'{validator.dialogue_count} dialogue files, {len(validator.speakers)} merged speakers.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
