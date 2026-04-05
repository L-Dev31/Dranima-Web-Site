# Copilot Workspace Instructions for Dranima Web Site

## Overview
This workspace contains the official website for the upcoming video game Dranima. It includes static HTML pages, JavaScript for dynamic features, CSS for styling, and a Python-based data editor for managing content.

## Key Conventions
- **Static Site**: All main pages are static HTML (see `index.html`, `wiki.html`, etc.).
- **Data Files**: Content is managed via JSON files in the `datas/` directory (e.g., `news.json`, `wiki.json`).
- **Editor**: `editor.py` is a Tkinter-based tool for editing JSON data files.
- **Scripts**: JavaScript files in `script/` handle dynamic UI features (e.g., news, wiki, credits, FAQ).
- **Assets**: Images, fonts, and partial HTML (navbar, footer, loader) are in `assets/`, `images/`, and `fonts/`.
- **Styling**: CSS files are organized by feature/page in `styles/`.

## Build & Test
- **No build step required**: Site is static and can be served by any HTTP server.
- **Testing**: Manual testing in browser is standard. No automated test suite is present.
- **Data Editing**: Use `editor.py` to update JSON files. Requires Python 3 and Tkinter. Optionally, install Pillow for image previews.

## Project Structure
- `index.html`, `wiki.html`, etc.: Main site pages
- `datas/`: JSON data files
- `script/`: JavaScript for dynamic features
- `styles/`: CSS stylesheets
- `assets/`: Shared HTML partials (navbar, footer, loader)
- `images/`, `fonts/`: Media assets
- `editor.py`: Data editor tool

## Pitfalls & Notes
- **Manual Data Consistency**: Edits to JSON files should be validated for syntax and structure.
- **No Automated Deployment**: Deployment is manual (e.g., GitHub Pages or custom host).
- **No Node.js or package.json**: No npm/yarn dependencies or build tools.

## Documentation
- See this file and in-code comments for guidance.
- For data editing, see docstrings in `editor.py`.

## Example Prompts
- "How do I update the news section?"
- "Where do I edit the FAQ content?"
- "How do I add a new wiki page?"
- "What is the purpose of editor.py?"

---

For advanced customization, consider creating agent instructions for:
- Data validation (JSON schema checks)
- Automated deployment (GitHub Actions)
- Accessibility or SEO audits

