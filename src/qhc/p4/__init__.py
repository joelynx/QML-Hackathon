"""Phase 4 code (E012 onward). Kept out of src/qhc/pipe/ so the pipeline revision of the scored arms stays fixed.

Each module is identified by its own hash; run manifests record
code_revision = "eval <evaluate.code_revision()> / pipe <pipe_revision()> / p4 <module> <module_revision(module)>".
"""
import hashlib
import os


def module_revision(name):
    """First 16 hex of sha256 over src/qhc/p4/<name>.py, line endings normalised to LF."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{name}.py"), "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()[:16]


def code_revision(name):
    from ..evaluate import code_revision as eval_revision
    from ..pipe import pipe_revision
    return f"eval {eval_revision()} / pipe {pipe_revision()} / p4 {name} {module_revision(name)}"
