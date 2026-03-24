import sys, os, argparse, fnmatch, json, csv, re, math
from collections import defaultdict

DEFAULT_EXCLUDE_DIRS = {
    ".git",".hg",".svn",".idea",".vscode",".venv","venv","node_modules","dist","build",
    ".next",".cache","__pycache__", ".mypy_cache",".pytest_cache",".turbo"
}
DEFAULT_INCLUDE_EXT = {
    ".py",".ipynb",".js",".jsx",".ts",".tsx",".md",".txt",".yml",".yaml",".toml",".ini",
    ".cfg",".html",".css",".scss",".sql",".csv",".env",".sh",".java",".kt",".go",".rb",".php",
    ".rs",".c",".h",".cpp",".hpp"
}
DEFAULT_MAX_MB = 5

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
    if "_" in tok: extra += tok.count("_")
    if tok and tok[0].isalpha() and tok.isascii():
        extra += len(_camel_boundary.findall(tok))
    return extra

def tokens_heuristic(text: str) -> int:
    base = tokens_bytes(text)
    ws_tokens = _ws_re.findall(text)
    expanded = 0
    for t in ws_tokens:
        expanded += 1 + _extra_splits_for_codey_token(t)
    return max(base, expanded)

ESTIMATORS = {
    "bytes": tokens_bytes,
    "chars": tokens_chars,
    "whitespace": tokens_whitespace,
    "heuristic": tokens_heuristic,
}

# ---------- Utilities ----------
def is_probably_text(path, max_probe=4096):
    try:
        with open(path,"rb") as f:
            chunk=f.read(max_probe)
            if b"\x00" in chunk: return False
            try:
                chunk.decode("utf-8")
                return True
            except:
                return False
    except:
        return False

def should_skip_dir(dirname, rel_dir, excludes, globs):
    rel_path = f"{rel_dir}/{dirname}" if rel_dir else dirname
    if dirname in excludes or rel_path in excludes: return True
    return any(
        fnmatch.fnmatch(dirname, g) or fnmatch.fnmatch(rel_path, g)
        for g in globs
    )

def load_gitignore(root):
    p=os.path.join(root,".gitignore")
    if not os.path.isfile(p): return []
    pats=[]
    with open(p,"r",encoding="utf-8",errors="ignore") as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith("#"): continue
            pats.append(s)
    return pats

def path_matches_patterns(root_rel, patterns):
    parts=root_rel.replace("\\","/").split("/")
    for pat in patterns:
        if "/" in pat:
            if fnmatch.fnmatch(root_rel, pat): return True
        else:
            if any(fnmatch.fnmatch(p, pat) for p in parts): return True
    return False

def human(n): return f"{n:,}"

# ---------- Main logic ----------
def scan(root, include_ext, exclude_dirs, exclude_globs, exclude_files, use_gitignore, max_mb, follow_symlinks, estimator):
    gitpats=load_gitignore(root) if use_gitignore else []
    results=[]
    for cur, dirs, files in os.walk(root, followlinks=follow_symlinks):
        rel=os.path.relpath(cur, root)
        if rel==".": rel=""
        dirs[:]=[d for d in dirs if not should_skip_dir(d, rel, exclude_dirs, exclude_globs)]
        if use_gitignore and rel and path_matches_patterns(rel, gitpats):
            dirs.clear(); continue
        for name in files:
            p=os.path.join(cur,name)
            relp=os.path.relpath(p, root).replace("\\","/")
            # File exclusion logic (new)
            if path_matches_patterns(relp, exclude_files): 
                continue
            if use_gitignore and path_matches_patterns(relp, gitpats): continue
            ext=os.path.splitext(name)[1].lower()
            if include_ext and ext not in include_ext: continue
            try:
                size=os.path.getsize(p)
                if size>(max_mb*1024*1024): continue
            except: continue
            if not is_probably_text(p): continue
            try:
                with open(p,"r",encoding="utf-8",errors="ignore") as f: txt=f.read()
                tok=estimator(txt)
                results.append({
                    "path":relp,"ext":ext or "",
                    "bytes":len(txt.encode('utf-8')), "chars":len(txt), "tokens":tok
                })
            except: continue
    return results

def aggregate_by_dir(rows, depth):
    agg=defaultdict(lambda: {"files":0,"tokens":0,"bytes":0})
    for r in rows:
        parts=r["path"].split(os.sep)
        key=os.path.join(*parts[:depth]) if depth>0 and parts else ""
        agg[key]["files"]+=1
        agg[key]["tokens"]+=r["tokens"]
        agg[key]["bytes"]+=r["bytes"]
    out=[]
    for k,v in agg.items():
        out.append({"dir":k or ".", "files":v["files"], "tokens":v["tokens"], "bytes":v["bytes"]})
    out.sort(key=lambda x:x["tokens"], reverse=True)
    return out

def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=fieldnames); w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

def write_json(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path,"w",encoding="utf-8") as f: json.dump(obj,f,ensure_ascii=False,indent=2)

def write_md(path, file_rows, dir_rows, totals, chart_paths=None):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path,"w",encoding="utf-8") as f:
        f.write(f"# Token Count Report (Estimated)\n\n")
        f.write(f"- Estimator: `{totals['estimator']}`\n- Files: **{human(totals['files'])}**\n- Total tokens (est.): **{human(totals['tokens'])}**\n- Total bytes: **{human(totals['bytes'])}**\n\n")
        if chart_paths:
            if chart_paths.get("dirs"):
                f.write("## Token Distribution by Directory (Chart)\n\n")
                f.write(f"![Top Directories by Tokens]({chart_paths['dirs']})\n\n")
            if chart_paths.get("files"):
                f.write("## Token Distribution by File (Chart)\n\n")
                f.write(f"![Top Files by Tokens]({chart_paths['files']})\n\n")
        f.write("## Top Directories by Tokens\n\n| Directory | Files | Tokens (est.) | Bytes |\n|---|---:|---:|---:|\n")
        for r in dir_rows[:20]: f.write(f"| {r['dir']} | {r['files']} | {human(r['tokens'])} | {human(r['bytes'])} |\n")
        f.write("\n## Top Files by Tokens\n\n| File | Ext | Tokens (est.) | Bytes |\n|---|---:|---:|---:|\n")
        for r in file_rows[:5000]: f.write(f"| {r['path']} | {r['ext']} | {human(r['tokens'])} | {human(r['bytes'])} |\n")

def render_charts(dir_rows, file_rows, out_dir, kind="bar", top=10, width=10, height=6, dpi=120):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("Chart rendering skipped (matplotlib not available). Install it with: pip install matplotlib", file=sys.stderr)
        return {}

    os.makedirs(out_dir, exist_ok=True)
    chart_paths={}

    top_dirs = dir_rows[:top]
    if top_dirs:
        labels=[r["dir"] or "." for r in top_dirs]
        values=[r["tokens"] for r in top_dirs]
        fig = plt.figure(figsize=(width, height), dpi=dpi)
        if kind=="pie":
            plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
            plt.title("Top Directories by Tokens (est.)")
        else:
            plt.bar(range(len(values)), values)
            plt.title("Top Directories by Tokens (est.)")
            plt.ylabel("Tokens (est.)")
            plt.xticks(range(len(labels)), labels, rotation=45, ha="right")
        plt.tight_layout()
        path=os.path.join(out_dir,"chart_dirs.png")
        plt.savefig(path); plt.close(fig)
        chart_paths["dirs"]="chart_dirs.png"

    top_files = file_rows[:top]
    if top_files:
        labels=[r["path"] for r in top_files]
        values=[r["tokens"] for r in top_files]
        fig = plt.figure(figsize=(width, height), dpi=dpi)
        if kind=="pie":
            plt.pie(values, labels=[os.path.basename(x) for x in labels], autopct="%1.1f%%", startangle=90)
            plt.title("Top Files by Tokens (est.)")
        else:
            plt.bar(range(len(values)), values)
            plt.title("Top Files by Tokens (est.)")
            plt.ylabel("Tokens (est.)")
            plt.xticks(range(len(labels)), [os.path.basename(x) for x in labels], rotation=45, ha="right")
        plt.tight_layout()
        path=os.path.join(out_dir,"chart_files.png")
        plt.savefig(path); plt.close(fig)
        chart_paths["files"]="chart_files.png"

    return chart_paths

def main():
    ap=argparse.ArgumentParser(prog="token_report", add_help=True)
    ap.add_argument("--root", default=".", help="project root (default: .)")
    ap.add_argument("--include-ext", default=",".join(sorted(DEFAULT_INCLUDE_EXT)), help="comma-separated list of file extensions")
    ap.add_argument("--exclude-dirs", default=",".join(sorted(DEFAULT_EXCLUDE_DIRS)), help="comma-separated list of directories to exclude")
    ap.add_argument("--exclude-globs", default="", help="extra glob patterns to exclude (e.g. *.lock,*.min.*)")
    ap.add_argument("--exclude-files", default="", help="comma-separated list of specific files to exclude (exact or wildcard)")
    ap.add_argument("--extra-exclude-dirs", default="", help="extra directories to exclude in addition to --exclude-dirs")
    ap.add_argument("--extra-exclude-globs", default="", help="extra glob patterns to exclude in addition to --exclude-globs")
    ap.add_argument("--extra-exclude-files", default="", help="extra file patterns to exclude in addition to --exclude-files")
    ap.add_argument("--use-gitignore", action="store_true", help="respect .gitignore rules")
    ap.add_argument("--max-mb", type=float, default=DEFAULT_MAX_MB, help="max file size in MB")
    ap.add_argument("--follow-symlinks", action="store_true", help="follow symbolic links")
    ap.add_argument("--depth", type=int, default=2, help="directory aggregation depth")
    ap.add_argument("--out-csv", default="token-report/files.csv")
    ap.add_argument("--out-json", default="token-report/files.json")
    ap.add_argument("--out-md", default="token-report/summary.md")
    ap.add_argument("--no-json", action="store_true")
    ap.add_argument("--no-md", action="store_true")
    ap.add_argument("--top", type=int, default=25, help="show top N items in stdout")
    ap.add_argument("--chart", action="store_true", help="render charts and embed in Markdown")
    ap.add_argument("--chart-kind", choices=["bar","pie"], default="bar", help="chart type")
    ap.add_argument("--chart-top", type=int, default=10, help="number of top items to plot")
    ap.add_argument("--chart-width", type=float, default=10, help="figure width inches")
    ap.add_argument("--chart-height", type=float, default=6, help="figure height inches")
    ap.add_argument("--chart-dpi", type=int, default=120, help="figure DPI")
    ap.add_argument("--estimator", choices=list(ESTIMATORS.keys()), default="bytes",
                    help="token estimator to use: bytes|chars|whitespace|heuristic (default: bytes)")

    args=ap.parse_args()

    include_ext=set([e.strip().lower() if e.strip().startswith(".") else "."+e.strip().lower() for e in args.include_ext.split(",") if e.strip()])
    exclude_dirs=set([d.strip() for d in args.exclude_dirs.split(",") if d.strip()])
    exclude_globs=[g.strip() for g in args.exclude_globs.split(",") if g.strip()]
    exclude_files=[f.strip() for f in args.exclude_files.split(",") if f.strip()]
    extra_exclude_dirs={d.strip() for d in args.extra_exclude_dirs.split(",") if d.strip()}
    extra_exclude_globs=[g.strip() for g in args.extra_exclude_globs.split(",") if g.strip()]
    extra_exclude_files=[f.strip() for f in args.extra_exclude_files.split(",") if f.strip()]
    exclude_dirs.update(extra_exclude_dirs)
    exclude_globs.extend(extra_exclude_globs)
    exclude_files.extend(extra_exclude_files)
    estimator = ESTIMATORS[args.estimator]

    rows=scan(args.root, include_ext, exclude_dirs, exclude_globs, exclude_files, args.use_gitignore, args.max_mb, args.follow_symlinks, estimator)
    rows.sort(key=lambda r:r["tokens"], reverse=True)
    totals={"estimator":args.estimator,"files":len(rows),"tokens":sum(r["tokens"] for r in rows),"bytes":sum(r["bytes"] for r in rows)}
    dir_rows=aggregate_by_dir(rows, args.depth)

    os.makedirs("token-report", exist_ok=True)
    write_csv(args.out_csv, rows, ["path","ext","tokens","bytes","chars"])
    if not args.no_json: write_json(args.out_json, {"totals":totals,"files":rows,"dirs":dir_rows})

    chart_paths=None
    if args.chart:
        chart_paths = render_charts(dir_rows, rows, out_dir=os.path.dirname(args.out_md) or ".",
                                    kind=args.chart_kind, top=args.chart_top,
                                    width=args.chart_width, height=args.chart_height, dpi=args.chart_dpi)

    if not args.no_md:
        write_md(args.out_md, rows, dir_rows, totals, chart_paths=chart_paths)

    print(f"Estimator: {totals['estimator']}")
    print(f"Files: {totals['files']}")
    print(f"Total tokens (est.): {totals['tokens']}")
    print(f"Total bytes: {totals['bytes']}")
    print("\nTop files by tokens (est.):")
    for r in rows[:args.top]: print(f"{r['tokens']:>10}  {r['bytes']:>10}  {r['path']}")
    print("\nTop directories by tokens (est.):")
    for r in dir_rows[:args.top]: print(f"{r['tokens']:>10}  {r['files']:>6}  {r['dir']}")

if __name__=="__main__": main()
