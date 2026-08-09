#!/usr/bin/env python3
"""Shared s-expression reader/writer for KiCad files.

The parser distinguishes quoted strings (Str) from bare symbols so that output
round-trips correctly -- KiCad rejects a file where a bare token got quoted or
vice versa.
"""

import re

TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')


class Str(str):
    """A token that was quoted in the source and must be quoted on output."""


def parse(text):
    stack, cur = [], []
    for m in TOKEN.finditer(text):
        t = m.group()
        if t == "(":
            new = []
            cur.append(new)
            stack.append(cur)
            cur = new
        elif t == ")":
            cur = stack.pop()
        elif t.startswith('"'):
            cur.append(Str(t[1:-1].replace('\\"', '"').replace("\\\\", "\\")))
        else:
            cur.append(t)
    return cur[0]


def dump(node, indent=0):
    if isinstance(node, list):
        pad = "  " * indent
        head = node[0] if node else ""
        parts = [dump(c, indent + 1) for c in node[1:]]
        # keep short forms on one line for readability
        one = f"({head} {' '.join(p.strip() for p in parts)})".rstrip()
        if len(one) < 110 and not any("\n" in p for p in parts):
            return pad + one
        body = "\n".join(parts)
        return f"{pad}({head}\n{body}\n{pad})"
    if isinstance(node, Str):
        esc = str(node).replace("\\", "\\\\").replace('"', '\\"')
        return "  " * indent + f'"{esc}"'
    return "  " * indent + str(node)


def kids(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def kid(node, name):
    k = kids(node, name)
    return k[0] if k else None


def drop(node, name):
    """Remove all direct children with the given head, in place."""
    node[:] = [c for c in node
               if not (isinstance(c, list) and c and c[0] == name)]
