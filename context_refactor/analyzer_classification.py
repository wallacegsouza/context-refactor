"""File classification helpers for analysis."""

from __future__ import annotations

import os

from .models import FileCategory

SOURCE_EXTS: set[str] = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
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
    ".cs",
    ".swift",
    ".scala",
    ".lua",
    ".sh",
    ".bash",
    ".zsh",
}

CONFIG_EXTS: set[str] = {
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".env",
    ".xml",
    ".properties",
    ".conf",
}

CONFIG_NAMES: set[str] = {
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "makefile",
    ".editorconfig",
    ".prettierrc",
    ".eslintrc",
    "tsconfig.json",
    "package.json",
    "pyproject.toml",
    "setup.cfg",
    "cargo.toml",
    "go.mod",
    "go.sum",
    "gemfile",
    "requirements.txt",
    "pipfile",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    ".gitignore",
    ".dockerignore",
    "vercel.json",
    "nest-cli.json",
    "vite.config.ts",
    "tailwind.config.ts",
    "postcss.config.js",
    "stryker.conf.cjs",
    "eslint.config.mjs",
    "eslint.config.js",
    "components.json",
}

MARKDOWN_EXTS: set[str] = {".md", ".mdx", ".rst"}

BINARY_EXTS: set[str] = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".o",
    ".a",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".wasm",
    ".pyc",
    ".class",
}


def classify_file(path: str, ext: str) -> FileCategory:
    """Return a :class:`FileCategory` for the given file path / extension."""
    ext_lower = ext.lower()
    name_lower = os.path.basename(path).lower()

    if ext_lower in BINARY_EXTS:
        return FileCategory.BINARY
    if ext_lower in MARKDOWN_EXTS:
        return FileCategory.MARKDOWN
    if ext_lower in CONFIG_EXTS or name_lower in CONFIG_NAMES:
        return FileCategory.CONFIGURATION
    if ext_lower in SOURCE_EXTS:
        return FileCategory.SOURCE_CODE
    if ext_lower in {".html", ".css", ".scss", ".sql", ".csv", ".txt"}:
        return FileCategory.OTHER
    return FileCategory.OTHER
