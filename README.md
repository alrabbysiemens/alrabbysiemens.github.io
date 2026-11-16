# alrabbysiemens.github.io

Personal website of **Al Rabby Siemens**, geographer (Dhaka, Bangladesh).

## How to update the site

**Easiest:** use the editing panel at <https://app.pagescms.org> - sign in with GitHub, open this repository, and use the forms (Write-ups, Latest updates, Publications, Gallery & videos …). Saving publishes the site in 1–2 minutes.

**Or edit files directly** on GitHub: everything you'd ever change lives in `content/`:

| File | What it holds |
|---|---|
| `content/profile.yml` | Name, tagline, roles, bio, links, photo, CV |
| `content/news.yml` | Latest updates (home page shows the top 3) |
| `content/publications.yml` | Books, chapters, journal articles, proceedings, op-eds |
| `content/projects.yml` | Projects and map dots |
| `content/experience.yml`, `education.yml`, `training.yml`, `skills.yml`, `awards.yml`, `languages.yml` | About pages |
| `content/beyond.yml` | Beyond Work: hometown, places, foods, trips, leadership |
| `content/media.yml` | Gallery photos and videos |
| `content/writeups/*.md` | One file per write-up (English or Bangla) |

Photos go in `static/img/` (gallery photos in `static/img/gallery/`), a public CV PDF in `static/cv/`.

## How it works

`build.py` turns `content/` + `templates/` into the finished site in `_site/`. A GitHub Action (`.github/workflows/deploy.yml`) runs it on every change and publishes to GitHub Pages.

Local preview: `pip install jinja2 pyyaml markdown && python build.py --preview`, then open `_site/index.html`.

Map: Bangladesh boundary from Natural Earth (public domain), via the `world-atlas` package.

## To do after the site goes public
- Add the two Bob Dylan "Blowin' in the Wind" lines at the end of `content/writeups/2023-01-26-school-college-bondhu.md`, just above the credit line (edit it in Pages CMS → Write-ups).

## "Your Presence" notes (visitor messages)
- Visitors leave a note in the pop-up window. Each note arrives in your email (the `guestbook_email` in `content/profile.yml`) via FormSubmit.
- The very first note triggers a one-time "Activate form" email from FormSubmit - click it, or notes won't arrive.
- To publish a note: Pages CMS → "Your Presence (visitor notes)" → add it (name, location, message, date) and tick **Approved**. Untick to hide it, delete the entry to remove it for good.
