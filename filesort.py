#!/usr/bin/env python3
"""
filesort - Intelligent File Organizer
Sorts messy directories by file type, date, or size.
"""

import os
import shutil
import argparse
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# File category definitions
CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff", ".heic", ".raw"],
    "Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md", ".rst", ".odt", ".rtf", ".csv"],
    "Archives": [".zip", ".tar", ".gz", ".bz2", ".7z", ".rar", ".zst", ".xz"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus"],
    "Video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "Code": [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".hpp", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".sh", ".bash", ".zsh", ".fish", ".yaml", ".yml", ".toml", ".json", ".xml", ".sql", ".css", ".scss", ".less", ".html"],
    "Config": [".env", ".ini", ".cfg", ".conf", ".editorconfig", ".gitignore", ".gitattributes", ".prettierrc", ".eslintrc", ".babelrc", ".npmrc"],
    "Executables": [".exe", ".msi", ".dmg", ".pkg", ".AppImage", ".deb", ".rpm", ".sh", ".bat"],
    "Fonts": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
    "Torrents": [".torrent", ".magnet"],
}

def get_category(filename):
    """Determine the category of a file based on its extension."""
    ext = Path(filename).suffix.lower()
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"

def get_file_date(filepath):
    """Get the modification date of a file."""
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime)

def analyze_directory(path, recursive=False):
    """Analyze a directory and return file info grouped by category."""
    files = []
    total_size = 0
    
    if recursive:
        iterator = Path(path).rglob("*")
    else:
        iterator = Path(path).glob("*")
    
    for f in iterator:
        if f.is_file() and not f.name.startswith("."):
            size = f.stat().st_size
            total_size += size
            files.append({
                "path": str(f),
                "name": f.name,
                "size": size,
                "category": get_category(f.name),
                "modified": get_file_date(f),
                "ext": f.suffix.lower(),
            })
    
    return files, total_size

def get_sort_key(file, sort_by):
    """Get the sort key for a file."""
    if sort_by == "type":
        return (file["category"], file["ext"])
    elif sort_by == "date":
        return file["modified"].strftime("%Y/%m")
    elif sort_by == "size":
        if file["size"] < 1024 * 100:  # < 100KB
            return "tiny"
        elif file["size"] < 1024 * 1024:  # < 1MB
            return "small"
        elif file["size"] < 1024 * 1024 * 100:  # < 100MB
            return "medium"
        else:
            return "large"
    return file["category"]

def format_size(size):
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def print_summary(files, total_size, dry_run):
    """Print a colorful summary of the analysis."""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    
    if dry_run:
        console.print("\n[bold yellow]🔍 DRY RUN - No files will be moved[/bold yellow]\n")
    else:
        console.print("\n[bold green]📦 Organizing files...[/bold green]\n")
    
    # Category breakdown
    cat_counts = defaultdict(int)
    cat_sizes = defaultdict(int)
    for f in files:
        cat_counts[f["category"]] += 1
        cat_sizes[f["category"]] += f["size"]
    
    table = Table(title=f"📊 Summary: {len(files)} files, {format_size(total_size)}")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right", style="yellow")
    table.add_column("Size", justify="right", style="green")
    
    for cat in sorted(cat_counts.keys()):
        table.add_row(cat, str(cat_counts[cat]), format_size(cat_sizes[cat]))
    
    console.print(table)

def organize_files(files, dest_dir, sort_by, dry_run, verbose, undo_file=None):
    """Organize files into subdirectories based on sort criteria."""
    operations = []
    
    for file in files:
        sort_key = get_sort_key(file, sort_by)
        target_dir = Path(dest_dir) / sort_key
        target_path = target_dir / file["name"]
        
        # Handle name conflicts
        if target_path.exists():
            stem = target_path.stem
            suffix = target_path.suffix
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{stem}_{counter}{suffix}"
                counter += 1
        
        operations.append({
            "source": file["path"],
            "target": str(target_path),
        })
    
    if dry_run:
        from rich.console import Console
        console = Console()
        console.print(f"\n[bold]Would organize into {dest_dir}/[/bold]")
        
        # Show sample (first 10 operations)
        sample = operations[:10]
        for op in sample:
            target = Path(op["target"])
            console.print(f"  📄 {Path(op['source']).name} → [cyan]{target.parent.name}/{target.name}[/cyan]")
        
        if len(operations) > 10:
            console.print(f"  ... and {len(operations) - 10} more files")
        
        return operations
    
    # Perform the moves
    moved = 0
    errors = 0
    undo_data = []
    
    from rich.progress import Progress, TextColumn, BarColumn
    from rich.console import Console
    console = Console()
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[green]Organizing...", total=len(operations))
        
        for op in operations:
            try:
                source_path = Path(op["source"])
                target_path = Path(op["target"])
                
                # Create target directory if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move the file
                shutil.move(str(source_path), str(target_path))
                moved += 1
                
                undo_data.append({
                    "source": str(target_path),
                    "target": str(source_path),
                })
                
                if verbose:
                    console.print(f"  📄 {source_path.name} → {target_path.parent.name}/")
                
            except Exception as e:
                console.print(f"  [red]❌ Error moving {op['source']}: {e}[/red]")
                errors += 1
            
            progress.update(task, advance=1)
    
    # Save undo file
    if undo_file and undo_data:
        with open(undo_file, "w") as f:
            json.dump(undo_data, f, indent=2)
        console.print(f"\n[green]✅ Moved {moved} files ({errors} errors)[/green]")
        console.print(f"💾 Undo file saved to: {undo_file}")
        console.print(f"   Run: [bold]filesort --undo {undo_file}[/bold]")
    
    return operations

def undo_operations(undo_file):
    """Undo a previous organization."""
    with open(undo_file) as f:
        operations = json.load(f)
    
    from rich.progress import Progress
    from rich.console import Console
    console = Console()
    
    restored = 0
    errors = 0
    
    with Progress() as progress:
        task = progress.add_task("[red]Undoing...", total=len(operations))
        
        for op in operations:
            try:
                source_path = Path(op["source"])
                target_path = Path(op["target"])
                
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_path), str(target_path))
                restored += 1
                
            except Exception as e:
                console.print(f"  [red]❌ Error: {e}[/red]")
                errors += 1
            
            progress.update(task, advance=1)
    
    console.print(f"\n[green]✅ Restored {restored} files ({errors} errors)[/green]")

def main():
    parser = argparse.ArgumentParser(
        description="📁 filesort - Intelligent File Organizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  filesort                    Analyze current directory
  filesort ~/Downloads        Organize Downloads folder by file type
  filesort . --by date        Sort by date (year/month folders)
  filesort . --by size        Sort by size (tiny/small/medium/large)
  filesort . --dry-run        Preview without making changes
  filesort . --recursive      Include subdirectories
  filesort --undo undo.json   Undo previous organization
  filesort . --dest Sorted    Output to 'Sorted/' directory
        """,
    )
    
    parser.add_argument("directory", nargs="?", default=".", help="Directory to organize")
    parser.add_argument("--by", choices=["type", "date", "size"], default="type", help="Sorting method")
    parser.add_argument("--dest", default=None, help="Destination directory (default: <source>/../Sorted_<type>)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't move files")
    parser.add_argument("--recursive", "-r", action="store_true", help="Include subdirectories")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    parser.add_argument("--undo", type=str, help="Undo a previous operation from JSON file")
    parser.add_argument("--version", action="version", version="filesort 1.0.0")
    
    args = parser.parse_args()
    
    # Handle undo
    if args.undo:
        undo_operations(args.undo)
        return
    
    source_dir = os.path.abspath(args.directory)
    
    if not os.path.isdir(source_dir):
        print(f"❌ Error: '{source_dir}' is not a valid directory")
        return 1
    
    # Set destination
    if args.dest:
        dest_dir = os.path.abspath(args.dest)
    else:
        parent = Path(source_dir).parent
        dir_name = Path(source_dir).name
        dest_dir = str(parent / f"{dir_name}_sorted_by_{args.by}")
    
    # Analyze
    if not args.quiet:
        from rich.console import Console
        console = Console()
        console.print(f"\n[bold]🔎 Analyzing: {source_dir}[/bold]")
        if args.recursive:
            console.print("   (recursive)")
    
    files, total_size = analyze_directory(source_dir, args.recursive)
    
    if not files:
        print("📭 No files found to organize.")
        return
    
    # Show summary
    if not args.quiet:
        print_summary(files, total_size, args.dry_run)
    
    # Undo filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    undo_file = f"filesort_undo_{timestamp}.json" if not args.dry_run else None
    
    # Organize
    organize_files(files, dest_dir, args.by, args.dry_run, args.verbose, undo_file)
    
    if not args.dry_run and not args.quiet:
        from rich.console import Console
        console = Console()
        console.print(f"\n[bold green]✅ Done! Files organized to: {dest_dir}[/bold green]")

if __name__ == "__main__":
    main()
