# 📁 filesort — Intelligent File Organizer

**Tired of a messy Downloads folder?** `filesort` automatically organizes your files into neat folders sorted by type, date, or size.

## ✨ Features

- **Sort by Type** — Images → `Images/`, Documents → `Documents/`, Code → `Code/`, etc.
- **Sort by Date** — Groups files into `2025/01/`, `2025/02/` folders by modification date
- **Sort by Size** — Categories: tiny (<100KB), small (<1MB), medium (<100MB), large (100MB+)
- **Dry Run Mode** — Preview changes before making them
- **Undo Support** — Every operation saves an undo file
- **Colorful CLI** — Beautiful Rich-powered terminal output
- **Safe** — Automatic name conflict resolution

## 🚀 Quick Start

```bash
# Install
pip install filesort

# Analyze current directory
filesort

# Organize Downloads by file type
filesort ~/Downloads

# Preview only (no changes)
filesort ~/Downloads --dry-run

# Sort by date
filesort ~/Documents --by date

# Sort by size
filesort ~/Desktop --by size

# Include subdirectories
filesort ~/Downloads -r

# Undo if you don't like the result
filesort --undo filesort_undo_20250101_120000.json
```

## 📦 Installation

```bash
pip install filesort
```

Requires Python 3.8+ and the `rich` library.

## 🎯 Use Cases

- **Clean your Downloads folder** — the #1 use case
- **Organize project directories** — Separate source code from assets
- **Sort photo backups** — By date for easy navigation
- **Tidy up desktops** — Quick cleanup before presentations

## 🔐 Safety

- **Dry-run mode** lets you preview everything before committing
- **Undo file** is saved automatically so you can revert any changes
- **Name conflicts** are handled gracefully with numbered suffixes

## 💖 Support

If you find this tool useful, consider buying me a coffee:

- [Buy on Gumroad](https://gumroad.com/l/filesort) — get priority support
- [Ko-fi](https://ko-fi.com/yourusername) — one-time tip
- ⭐ Star on GitHub — it helps others find the project

## 📄 License

MIT
