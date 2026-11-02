"""Build the Deep Chats static site.

Validates the JSON dataset in data/ against data/schema.json, then uses
Flask + Frozen-Flask to render the templates into build/ and copy the
result to docs/ (which GitHub Pages serves).
"""

import json
import os
import shutil
import subprocess
import sys
import time

try:
    import jsonschema
except ImportError:  # pragma: no cover
    sys.exit('Missing dependency: run "pip install -r requirements.txt"')

from flask import Flask, render_template, request, url_for
from flask_frozen import Freezer

app = Flask(__name__)
freezer = Freezer(app)

DATA_FOLDER = 'data'
SCHEMA_PATH = os.path.join(DATA_FOLDER, 'schema.json')
BUILD_FOLDER = 'build'
SITE_FOLDER = 'docs'

data = []
id_to_question = {}


# --------------------------------------------------------------------------
# URL helper: relative links so the site works both when previewed locally
# and when hosted under a sub-path (e.g. GitHub Pages at /deepchats/).
# --------------------------------------------------------------------------
def rel_url(endpoint, **values):
    depth = max(0, len([p for p in request.path.split('/') if p]) - 1)
    target = ('../' * depth) + url_for(endpoint, **values).lstrip('/')
    return target if target else './'


@app.context_processor
def inject_helpers():
    return {'rel_url': rel_url}


# --------------------------------------------------------------------------
# Data loading + validation
# --------------------------------------------------------------------------
def load_schema():
    with open(SCHEMA_PATH, encoding='utf-8') as schema_file:
        return json.load(schema_file)


def load_data():
    """Load every question file in data/, validating it as we go.

    Exits with a non-zero status (and a readable report) if any file is
    invalid, so broken data can never silently reach the built site.
    """
    global data, id_to_question
    schema = load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    problems = []
    items = []

    for filename in sorted(os.listdir(DATA_FOLDER)):
        path = os.path.join(DATA_FOLDER, filename)
        if not os.path.isfile(path) or not filename.endswith('.json'):
            continue
        if filename == os.path.basename(SCHEMA_PATH):
            continue
        try:
            with open(path, encoding='utf-8') as json_file:
                item = json.load(json_file)
        except json.JSONDecodeError as exc:
            problems.append(f'{filename}: invalid JSON ({exc})')
            continue

        for error in validator.iter_errors(item):
            location = '.'.join(str(part) for part in error.path) or '<root>'
            problems.append(f'{filename}: {location}: {error.message}')
        items.append((filename, item))

    # Cross-file checks: unique ids, matching file names, resolvable links.
    seen_ids = {}
    for filename, item in items:
        if not isinstance(item, dict):
            continue
        item_id = item.get('id')
        if not isinstance(item_id, int):
            continue
        if item_id in seen_ids:
            problems.append(
                f'{filename}: duplicate id {item_id} (already used by {seen_ids[item_id]})'
            )
        seen_ids[item_id] = filename
        if filename != f'{item_id}.json':
            problems.append(f'{filename}: file name must match the id ({item_id}.json)')
    for filename, item in items:
        if not isinstance(item, dict):
            continue
        for related_id in item.get('related_id', []):
            if related_id not in seen_ids:
                problems.append(
                    f'{filename}: related_id {related_id} does not match any question id'
                )

    if problems:
        print('Data validation failed:')
        for problem in problems:
            print(f'  - {problem}')
        sys.exit(1)

    data = [item for _, item in items]
    data.sort(key=lambda item: item['id'])
    id_to_question = {item['id']: item['question'] for item in data}
    for item in data:
        item['related'] = [
            {'id': related_id, 'question': id_to_question[related_id]}
            for related_id in item.get('related_id', [])
        ]


def tag_counts():
    counts = {}
    for item in data:
        for tag in item.get('tags', []):
            counts[tag] = counts.get(tag, 0) + 1
    return dict(sorted(counts.items()))


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html', data=data)


@app.route('/about.html')
def about():
    return render_template('about.html')


@app.route('/tags/index.html')
def tags_index():
    # NOTE: /tags.html must stay a separate endpoint — Flask-Freeze resolves
    # one URL per endpoint, so sharing a function would drop one of the files.
    return render_template('tags.html', tag_counts=tag_counts())


@app.route('/tags.html')
def tag_list():
    return render_template('tags.html', tag_counts=tag_counts())


@app.route('/tags/<tag>.html')
def tags(tag):
    filtered_data = [item for item in data if tag in item.get('tags', [])]
    return render_template('index.html', data=filtered_data)


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------
def remove_tree(path, attempts=3):
    """Remove a directory, retrying briefly (OneDrive can hold locks).

    Falls back to `rmdir /s /q`, which copes with OneDrive's sync handles
    better than shutil.rmtree on Windows.
    """
    for attempt in range(1, attempts + 1):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            if os.name == 'nt':
                result = subprocess.run(
                    ['cmd', '/c', 'rmdir', '/s', '/q', path],
                    capture_output=True,
                )
                if result.returncode == 0 and not os.path.exists(path):
                    return
            if attempt == attempts:
                raise
            time.sleep(1)


def freeze_site():
    # Rebuild from scratch so removed pages don't linger as stale files.
    if os.path.exists(BUILD_FOLDER):
        remove_tree(BUILD_FOLDER)
    freezer.freeze()
    # Copy (not move) the fresh build over docs/ so both stay in sync.
    if os.path.exists(SITE_FOLDER):
        remove_tree(SITE_FOLDER)
    shutil.copytree(BUILD_FOLDER, SITE_FOLDER)


load_data()

if __name__ == '__main__':
    freeze_site()
    print(f'Frozen {len(data)} questions into {BUILD_FOLDER}/ and {SITE_FOLDER}/')
