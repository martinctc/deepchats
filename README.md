# Compendium of Questions for Deep and Meaningful Chats

## Summary

This is a demo Flask project that takes in a hierarchical dataset stored in JSON, and transforms it into a static HTML website that enables users to browse through cards with tags, related cards, and a search bar.

## Motivations

Small talk helps people build rapport, but it is through deep and meaningful conversations (DMCs) where people build intimacy and truly learn about each other. This demo website contains cards that you can use to kick start a DMC, if you are struggling to think of good questions to talk about.

## Features

- **Search** — fuzzy, client-side search across questions, descriptions, and tags (powered by [Fuse.js](https://fusejs.io/)). Searches are shareable via `?q=...` URLs.
- **Tags** — every question is tagged; the tag index shows how many questions use each tag.
- **Related questions** — each card links to similar questions.
- **Dark mode** — toggle in the navigation bar; the choice is remembered, and the site follows your system preference by default.
- **Surprise me** — picks a random question and scrolls to it.
- **Data validation** — every `data/*.json` file is validated against `data/schema.json` before the site builds, so broken data fails fast with a readable report.

## Previewing the site

Install the dependencies (once):
```
pip install -r requirements.txt
```

From the directory, run this in Command Prompt:
```
python init.py
```

The static website files will be created in the `build` sub-directory and copied to `docs`, which can then be hosted through GitHub Pages.

## Adding or editing questions

Questions live in `data/<id>.json` and must match `data/schema.json`:

```json
{
  "id": 10,
  "question": "What are the three most important values in your life?",
  "description": "Why this question works.",
  "related_id": [],
  "tags": ["intimate"]
}
```

Rules enforced at build time:

- `id` must be unique and the file must be named `<id>.json`
- `question` and `description` must be at least 10 characters
- `related_id` entries must point to existing question ids
- `tags` must contain at least one tag

If anything is wrong, `python init.py` prints every problem and exits with a non-zero status.

## Notes

- `templates/index.html` determines the template for the main page and question cards.
- `templates/base.html` provides the base HTML design, navigation, and search form for the site.
- `templates/tags.html` provides a summary of all the tags used in the JSON dataset.
- `static/style.css` contains the custom styles (including the dark theme).
- `static/search.js` contains the search, theme toggle, and "Surprise me" logic.
- `data/*.json` are JSON files that contain the data for the site; `data/schema.json` describes their structure.
