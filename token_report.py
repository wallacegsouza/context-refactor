import argparse
import csv
import fnmatch
import json
import math
import os
import re
import sys
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".cache",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".turbo",
}
DEFAULT_INCLUDE_EXT = {
    ".py",
    ".ipynb",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".html",
    ".css",
    ".scss",
    ".sql",
    ".csv",
    ".env",
    ".sh",
    ".java",
    ".kt",
    ".go",
    ".rb",
    ".php",
    ".rs",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
}
DEFAULT_MAX_MB = 5
DEFAULT_OUTPUT_DIR = "token-report"

# ---------- Token estimators ----------
_ws_re = re.compile(r"\S+")
_camel_boundary = re.compile(r"(?<!^)(?=[A-Z])")


def tokens_bytes(text: str) -> int:
    return math.ceil(len(text.encode("utf-8")) / 4)


def tokens_chars(text: str) -> int:
    return math.ceil(len(text) / 4)


def tokens_whitespace(text: str) -> int:
    return len(_ws_re.findall(text))


def _extra_splits_for_codey_token(tok: str) -> int:
    extra = 0
    if "_" in tok:
        extra += tok.count("_")
    if tok and tok[0].isalpha() and tok.isascii():
        extra += len(_camel_boundary.findall(tok))
    return extra


def tokens_heuristic(text: str) -> int:
    base = tokens_bytes(text)
    ws_tokens = _ws_re.findall(text)
    expanded = 0
    for token in ws_tokens:
        expanded += 1 + _extra_splits_for_codey_token(token)
    return max(base, expanded)


ESTIMATORS = {
    "bytes": tokens_bytes,
    "chars": tokens_chars,
    "whitespace": tokens_whitespace,
    "heuristic": tokens_heuristic,
}


@dataclass(frozen=True)
class RuntimeConfig:
    root: str
    include_ext: set[str]
    exclude_dirs: set[str]
    exclude_globs: list[str]
    exclude_files: list[str]
    use_gitignore: bool
    max_mb: float
    follow_symlinks: bool
    depth: int
    out_csv: str
    out_json: str
    out_md: str
    write_json: bool
    write_md: bool
    top: int
    chart: bool
    chart_kind: str
    chart_top: int
    chart_width: float
    chart_height: float
    chart_dpi: int
    estimator_name: str
    estimator: Callable[[str], int]


# ---------- Utilities ----------
def is_probably_text(path, max_probe=4096):
    try:
        with open(path, "rb") as handle:
            chunk = handle.read(max_probe)
            if b"\x00" in chunk:
                return False
            try:
                chunk.decode("utf-8")
                return True
            except Exception:
                return False
    except Exception:
        return False


def should_skip_dir(dirname, rel_dir, excludes, globs):
    rel_path = f"{rel_dir}/{dirname}" if rel_dir else dirname
    if dirname in excludes or rel_path in excludes:
        return True
    return any(
        fnmatch.fnmatch(dirname, pattern) or fnmatch.fnmatch(rel_path, pattern) for pattern in globs
    )


def load_gitignore(root):
    path = os.path.join(root, ".gitignore")
    if not os.path.isfile(path):
        return []
    patterns = []
    with open(path, encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            patterns.append(stripped)
    return patterns


def path_matches_patterns(root_rel, patterns):
    parts = root_rel.replace("\\", "/").split("/")
    for pattern in patterns:
        if "/" in pattern:
            if fnmatch.fnmatch(root_rel, pattern):
                return True
        elif any(fnmatch.fnmatch(part, pattern) for part in parts):
            return True
    return False


def human(number):
    return f"{number:,}"


def csv_items(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_include_extensions(value: str) -> set[str]:
    normalized: set[str] = set()
    for extension in csv_items(value):
        normalized.add(extension.lower() if extension.startswith(".") else f".{extension.lower()}")
    return normalized


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="token_report", add_help=True)
    parser.add_argument("--root", default=".", help="project root (default: .)")
    parser.add_argument(
        "--include-ext",
        default=",".join(sorted(DEFAULT_INCLUDE_EXT)),
        help="comma-separated list of file extensions",
    )
    parser.add_argument(
        "--exclude-dirs",
        default=",".join(sorted(DEFAULT_EXCLUDE_DIRS)),
        help="comma-separated list of directories to exclude",
    )
    parser.add_argument(
        "--exclude-globs", default="", help="extra glob patterns to exclude (e.g. *.lock,*.min.*)"
    )
    parser.add_argument(
        "--exclude-files",
        default="",
        help="comma-separated list of specific files to exclude (exact or wildcard)",
    )
    parser.add_argument(
        "--extra-exclude-dirs",
        default="",
        help="extra directories to exclude in addition to --exclude-dirs",
    )
    parser.add_argument(
        "--extra-exclude-globs",
        default="",
        help="extra glob patterns to exclude in addition to --exclude-globs",
    )
    parser.add_argument(
        "--extra-exclude-files",
        default="",
        help="extra file patterns to exclude in addition to --exclude-files",
    )
    parser.add_argument("--use-gitignore", action="store_true", help="respect .gitignore rules")
    parser.add_argument("--max-mb", type=float, default=DEFAULT_MAX_MB, help="max file size in MB")
    parser.add_argument("--follow-symlinks", action="store_true", help="follow symbolic links")
    parser.add_argument("--depth", type=int, default=2, help="directory aggregation depth")
    parser.add_argument("--out-csv", default=f"{DEFAULT_OUTPUT_DIR}/files.csv")
    parser.add_argument("--out-json", default=f"{DEFAULT_OUTPUT_DIR}/files.json")
    parser.add_argument("--out-md", default=f"{DEFAULT_OUTPUT_DIR}/summary.md")
    parser.add_argument("--no-json", action="store_true")
    parser.add_argument("--no-md", action="store_true")
    parser.add_argument("--top", type=int, default=25, help="show top N items in stdout")
    parser.add_argument("--chart", action="store_true", help="render charts and embed in Markdown")
    parser.add_argument("--chart-kind", choices=["bar", "pie"], default="bar", help="chart type")
    parser.add_argument("--chart-top", type=int, default=10, help="number of top items to plot")
    parser.add_argument("--chart-width", type=float, default=10, help="figure width inches")
    parser.add_argument("--chart-height", type=float, default=6, help="figure height inches")
    parser.add_argument("--chart-dpi", type=int, default=120, help="figure DPI")
    parser.add_argument(
        "--estimator",
        choices=list(ESTIMATORS.keys()),
        default="bytes",
        help="token estimator to use: bytes|chars|whitespace|heuristic (default: bytes)",
    )
    return parser


def build_runtime_config(args: argparse.Namespace) -> RuntimeConfig:
    exclude_dirs = set(csv_items(args.exclude_dirs))
    exclude_globs = csv_items(args.exclude_globs)
    exclude_files = csv_items(args.exclude_files)

    exclude_dirs.update(csv_items(args.extra_exclude_dirs))
    exclude_globs.extend(csv_items(args.extra_exclude_globs))
    exclude_files.extend(csv_items(args.extra_exclude_files))

    return RuntimeConfig(
        root=args.root,
        include_ext=normalize_include_extensions(args.include_ext),
        exclude_dirs=exclude_dirs,
        exclude_globs=exclude_globs,
        exclude_files=exclude_files,
        use_gitignore=args.use_gitignore,
        max_mb=args.max_mb,
        follow_symlinks=args.follow_symlinks,
        depth=args.depth,
        out_csv=args.out_csv,
        out_json=args.out_json,
        out_md=args.out_md,
        write_json=not args.no_json,
        write_md=not args.no_md,
        top=args.top,
        chart=args.chart,
        chart_kind=args.chart_kind,
        chart_top=args.chart_top,
        chart_width=args.chart_width,
        chart_height=args.chart_height,
        chart_dpi=args.chart_dpi,
        estimator_name=args.estimator,
        estimator=ESTIMATORS[args.estimator],
    )


# ---------- Main logic ----------
def scan(
    root,
    include_ext,
    exclude_dirs,
    exclude_globs,
    exclude_files,
    use_gitignore,
    max_mb,
    follow_symlinks,
    estimator,
):
    git_patterns = load_gitignore(root) if use_gitignore else []
    results = []
    for current_dir, dirs, files in os.walk(root, followlinks=follow_symlinks):
        rel_dir = os.path.relpath(current_dir, root)
        if rel_dir == ".":
            rel_dir = ""
        dirs[:] = [
            dirname
            for dirname in dirs
            if not should_skip_dir(dirname, rel_dir, exclude_dirs, exclude_globs)
        ]
        if use_gitignore and rel_dir and path_matches_patterns(rel_dir, git_patterns):
            dirs.clear()
            continue
        for name in files:
            path = os.path.join(current_dir, name)
            rel_path = os.path.relpath(path, root).replace("\\", "/")
            if path_matches_patterns(rel_path, exclude_files):
                continue
            if use_gitignore and path_matches_patterns(rel_path, git_patterns):
                continue
            ext = os.path.splitext(name)[1].lower()
            if include_ext and ext not in include_ext:
                continue
            try:
                size = os.path.getsize(path)
                if size > (max_mb * 1024 * 1024):
                    continue
            except Exception:
                continue
            if not is_probably_text(path):
                continue
            try:
                with open(path, encoding="utf-8", errors="ignore") as handle:
                    text = handle.read()
            except Exception:
                continue
            results.append(
                {
                    "path": rel_path,
                    "ext": ext or "",
                    "bytes": len(text.encode("utf-8")),
                    "chars": len(text),
                    "tokens": estimator(text),
                }
            )
    return results


def aggregate_by_dir(rows, depth):
    aggregate = defaultdict(lambda: {"files": 0, "tokens": 0, "bytes": 0})
    for row in rows:
        parts = row["path"].split(os.sep)
        key = os.path.join(*parts[:depth]) if depth > 0 and parts else ""
        aggregate[key]["files"] += 1
        aggregate[key]["tokens"] += row["tokens"]
        aggregate[key]["bytes"] += row["bytes"]
    output = []
    for key, values in aggregate.items():
        output.append(
            {
                "dir": key or ".",
                "files": values["files"],
                "tokens": values["tokens"],
                "bytes": values["bytes"],
            }
        )
    output.sort(key=lambda item: item["tokens"], reverse=True)
    return output


def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(obj, handle, ensure_ascii=False, indent=2)


def write_md(path, file_rows, dir_rows, totals, chart_paths=None):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("# Token Count Report (Estimated)\n\n")
        handle.write(
            f"- Estimator: `{totals['estimator']}`\n"
            f"- Files: **{human(totals['files'])}**\n"
            f"- Total tokens (est.): **{human(totals['tokens'])}**\n"
            f"- Total bytes: **{human(totals['bytes'])}**\n\n"
        )
        if chart_paths:
            if chart_paths.get("dirs"):
                handle.write("## Token Distribution by Directory (Chart)\n\n")
                handle.write(f"![Top Directories by Tokens]({chart_paths['dirs']})\n\n")
            if chart_paths.get("files"):
                handle.write("## Token Distribution by File (Chart)\n\n")
                handle.write(f"![Top Files by Tokens]({chart_paths['files']})\n\n")
        handle.write(
            "## Top Directories by Tokens\n\n| Directory | Files | Tokens (est.) | Bytes |\n|---|---:|---:|---:|\n"
        )
        for row in dir_rows[:20]:
            handle.write(
                f"| {row['dir']} | {row['files']} | {human(row['tokens'])} | {human(row['bytes'])} |\n"
            )
        handle.write(
            "\n## Top Files by Tokens\n\n| File | Ext | Tokens (est.) | Bytes |\n|---|---:|---:|---:|\n"
        )
        for row in file_rows[:5000]:
            handle.write(
                f"| {row['path']} | {row['ext']} | {human(row['tokens'])} | {human(row['bytes'])} |\n"
            )


def render_charts(dir_rows, file_rows, out_dir, kind="bar", top=10, width=10, height=6, dpi=120):
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print(
            "Chart rendering skipped (matplotlib not available). Install it with: pip install matplotlib",
            file=sys.stderr,
        )
        return {}

    os.makedirs(out_dir, exist_ok=True)
    chart_paths = {}

    top_dirs = dir_rows[:top]
    if top_dirs:
        labels = [row["dir"] or "." for row in top_dirs]
        values = [row["tokens"] for row in top_dirs]
        fig = plt.figure(figsize=(width, height), dpi=dpi)
        if kind == "pie":
            plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
            plt.title("Top Directories by Tokens (est.)")
        else:
            plt.bar(range(len(values)), values)
            plt.title("Top Directories by Tokens (est.)")
            plt.ylabel("Tokens (est.)")
            plt.xticks(range(len(labels)), labels, rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "chart_dirs.png"))
        plt.close(fig)
        chart_paths["dirs"] = "chart_dirs.png"

    top_files = file_rows[:top]
    if top_files:
        labels = [row["path"] for row in top_files]
        values = [row["tokens"] for row in top_files]
        fig = plt.figure(figsize=(width, height), dpi=dpi)
        if kind == "pie":
            plt.pie(
                values,
                labels=[os.path.basename(label) for label in labels],
                autopct="%1.1f%%",
                startangle=90,
            )
            plt.title("Top Files by Tokens (est.)")
        else:
            plt.bar(range(len(values)), values)
            plt.title("Top Files by Tokens (est.)")
            plt.ylabel("Tokens (est.)")
            plt.xticks(
                range(len(labels)),
                [os.path.basename(label) for label in labels],
                rotation=45,
                ha="right",
            )
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "chart_files.png"))
        plt.close(fig)
        chart_paths["files"] = "chart_files.png"

    return chart_paths


def generate_report(config: RuntimeConfig):
    rows = scan(
        config.root,
        config.include_ext,
        config.exclude_dirs,
        config.exclude_globs,
        config.exclude_files,
        config.use_gitignore,
        config.max_mb,
        config.follow_symlinks,
        config.estimator,
    )
    rows.sort(key=lambda row: row["tokens"], reverse=True)
    totals = {
        "estimator": config.estimator_name,
        "files": len(rows),
        "tokens": sum(row["tokens"] for row in rows),
        "bytes": sum(row["bytes"] for row in rows),
    }
    dir_rows = aggregate_by_dir(rows, config.depth)
    return rows, dir_rows, totals


def write_outputs(config: RuntimeConfig, rows, dir_rows, totals):
    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
    write_csv(config.out_csv, rows, ["path", "ext", "tokens", "bytes", "chars"])
    if config.write_json:
        write_json(config.out_json, {"totals": totals, "files": rows, "dirs": dir_rows})

    chart_paths = None
    if config.chart:
        chart_paths = render_charts(
            dir_rows,
            rows,
            out_dir=os.path.dirname(config.out_md) or ".",
            kind=config.chart_kind,
            top=config.chart_top,
            width=config.chart_width,
            height=config.chart_height,
            dpi=config.chart_dpi,
        )

    if config.write_md:
        write_md(config.out_md, rows, dir_rows, totals, chart_paths=chart_paths)


def print_report_summary(rows, dir_rows, totals, top):
    print(f"Estimator: {totals['estimator']}")
    print(f"Files: {totals['files']}")
    print(f"Total tokens (est.): {totals['tokens']}")
    print(f"Total bytes: {totals['bytes']}")
    print("\nTop files by tokens (est.):")
    for row in rows[:top]:
        print(f"{row['tokens']:>10}  {row['bytes']:>10}  {row['path']}")
    print("\nTop directories by tokens (est.):")
    for row in dir_rows[:top]:
        print(f"{row['tokens']:>10}  {row['files']:>6}  {row['dir']}")


def main():
    args = create_argument_parser().parse_args()
    config = build_runtime_config(args)
    rows, dir_rows, totals = generate_report(config)
    write_outputs(config, rows, dir_rows, totals)
    print_report_summary(rows, dir_rows, totals, config.top)


if __name__ == "__main__":
    main()
