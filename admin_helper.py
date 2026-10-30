"""Administration helpers. Cascades are derived from the ON DELETE CASCADE foreign keys in the schema."""
from sqlalchemy import delete, select

from db import db

SECTIONS = [
    ("authorization_codes", "Authorization codes"),
    ("users", "Users"),
    ("games", "Games"),
    ("puzzles", "Puzzles"),
    ("answers", "Answers"),
]
HIDDEN_COLUMNS = {"users": {"password"}}
ROW_LIMIT = 500


def _table(name):
    if name not in dict(SECTIONS):
        return None
    return db.metadata.tables[name]


def _primary_key(table):
    return list(table.primary_key.columns)[0]


def _coerce(table, value):
    try:
        return _primary_key(table).type.python_type(value)
    except (TypeError, ValueError, NotImplementedError):
        return None


def cascade_preview(table_name, key):
    """Return {table: [primary keys]} of every row removed along with the given row, or None if it doesn't exist."""
    root = _table(table_name)
    if root is None:
        return None
    key = _coerce(root, key)
    if key is None:
        return None
    if db.session.execute(select(_primary_key(root)).where(_primary_key(root) == key)).first() is None:
        return None

    found = {table_name: {key}}
    queue = [table_name]
    while queue:
        parent = queue.pop(0)
        for child in db.metadata.tables.values():
            for fk in child.foreign_keys:
                if fk.column.table.name != parent or fk.constraint.ondelete != "CASCADE":
                    continue
                rows = db.session.execute(
                    select(_primary_key(child)).where(fk.parent.in_(found[parent]))
                ).scalars().all()
                known = found.setdefault(child.name, set())
                new = set(rows) - known
                if new:
                    known |= new
                    queue.append(child.name)

    found[table_name].discard(key)
    return {name: sorted(ids) for name, ids in found.items() if ids}


def lockout_preview(table_name, key):
    """Return {table: [primary keys]} of rows whose foreign key is set to NULL (ON DELETE SET NULL)."""
    root = _table(table_name)
    key = _coerce(root, key) if root is not None else None
    result = {}
    if key is None:
        return result
    for child in db.metadata.tables.values():
        for fk in child.foreign_keys:
            if fk.column.table.name == table_name and fk.constraint.ondelete == "SET NULL":
                rows = db.session.execute(select(_primary_key(child)).where(fk.parent == key)).scalars().all()
                if rows:
                    result[child.name] = sorted(rows)
    return result


def delete_row(table_name, key):
    table = _table(table_name)
    db.session.execute(delete(table).where(_primary_key(table) == _coerce(table, key)))
    db.session.commit()


def section_rows():
    sections = []
    for name, title in SECTIONS:
        table = db.metadata.tables[name]
        columns = [c for c in table.columns if c.name not in HIDDEN_COLUMNS.get(name, ())]
        pk = _primary_key(table)
        rows = db.session.execute(select(*columns).order_by(pk.desc()).limit(ROW_LIMIT + 1)).all()
        sections.append({
            "name": name,
            "title": title,
            "columns": [c.name for c in columns],
            "pk": pk.name,
            "rows": rows[:ROW_LIMIT],
            "truncated": len(rows) > ROW_LIMIT,
        })
    return sections
