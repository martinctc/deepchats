# Compendium of Questions for Deep and Meaningful Chats

## Summary

This is a demo Flask project that takes in a hierarchical dataset stored in JSON, and transforms it into a static HTML website that enables users to browse through cards with tags, related cards, and a search bar.

## Motivations

Small talk helps people build rapport, but it is through deep and meaningful conversations (DMCs) where people build intimacy and truly learn about each other. This demo website contains cards that you can use to kick start a DMC, if you are struggling to think of good questions to talk about. 

## Previewing the site

From the directory, run this in Command Prompt: 
```
python init.py
```

The static website files will be created in the `build` sub-directory, and renamed to `docs`, which can then be hosted through GitHub Pages.

## Notes

- `index.html` determines the template for the main page.
- `base.html` provides the base HTML design for the site.
- `tags.html` provides a summary of all the tags used in the JSON dataset. 
- `data/*.json` are JSON files that contain the data for the site.