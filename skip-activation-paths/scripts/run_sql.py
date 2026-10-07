"""
Run every file in sql/ against the synthetic CSVs.

The SQL is written in Snowflake dialect. To validate it locally we transpile each
statement to DuckDB with sqlglot and execute it. Every query whose comment starts
with `-- Q:` is saved to analysis/sql_results/<file>__<n>.csv and printed.

Usage:  python scripts/run_sql.py            # all files
        python scripts/run_sql.py 03 05      # selected files
"""
import re
import sys
from pathlib import Path

import duckdb
import sqlglot

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
OUT = ROOT / "analysis" / "sql_results"
OUT.mkdir(parents=True, exist_ok=True)

con = None


def load_tables():
    global con
    con = duckdb.connect()
    for t in ["users", "events", "subscriptions", "drawing_calendar"]:
        con.execute(f"CREATE TABLE {t} AS SELECT * FROM read_csv_auto('{ROOT / 'data' / (t + '.csv')}')")
    return con


def get_connection():
    """Load the CSVs and build every view defined in sql/ (no printing). Used by analysis/."""
    load_tables()
    for f in sorted(SQL_DIR.glob("*.sql")):
        run_file(f, show=False)
    return con


def statements(text):
    # split on semicolons at line end (no semicolons inside our string literals)
    parts = re.split(r";\s*\n", text)
    return [p.strip() for p in parts if re.sub(r"--.*", "", p).strip()]


def run_file(path, show=True):
    raw = path.read_text()
    q = 0
    for stmt in statements(raw):
        title = None
        m = re.search(r"--\s*Q:\s*(.+)", stmt)
        if m:
            title = m.group(1).strip()
        body = "\n".join(l for l in stmt.splitlines() if not l.strip().startswith("--"))
        duck = sqlglot.transpile(body, read="snowflake", write="duckdb")[0]
        try:
            res = con.execute(duck)
        except Exception as exc:  # surface the transpiled SQL for debugging
            print(f"\n!! {path.name} failed:\n{duck}\n{exc}")
            raise
        if title:
            q += 1
            df = res.df()
            df.to_csv(OUT / f"{path.stem}__{q:02d}.csv", index=False)
            if show:
                print(f"\n=== {path.name} — Q{q}: {title}  ({len(df)} rows)")
                with __import__("pandas").option_context("display.width", 200, "display.max_columns", 30,
                                                         "display.max_rows", 40):
                    print(df.head(40).to_string(index=False))


def main():
    load_tables()
    files = sorted(SQL_DIR.glob("*.sql"))
    sel = sys.argv[1:]
    run_file(files[0], show=False)  # staging always runs
    for f in files[1:]:  # later files depend on views created by earlier ones
        run_file(f, show=(not sel or any(f.name.startswith(s) for s in sel)))


if __name__ == "__main__":
    main()
