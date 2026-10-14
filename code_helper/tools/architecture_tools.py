"""Architecture mapper tools.

Provides list_project_files and inspect_imports for deterministic
analysis of Python codebases, along with graph building, deterministic Mermaid
and draw.io XML generation, and structured architecture reporting.
"""

import ast
import fnmatch
import html
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any


def get_default_project_root() -> str:
    """Get the absolute path to the target_project directory."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "target_project",
    )


def list_project_files() -> str:
    """List relevant Python project files, excluding irrelevant directories.

    Uses Python to list .py files while excluding:
    - .git directory
    - .venv and virtual environments
    - Cache directories (__pycache__)
    - Secrets and sensitive files
    - Generated/irrelevant content

    Returns:
        String listing discovered .py files and their paths,
        or error message if no files found.
    """
    base_dir = get_default_project_root()

    if not os.path.isdir(base_dir):
        return f"Error: Target project directory not found: {base_dir}"

    excluded_dirs = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "build",
        "dist",
        "*.egg-info",
    }

    excluded_extensions = {".pyc", ".so", ".pyd", ".db", ".json", ".toml", ".cfg"}

    discovered = []

    try:
        for root, dirs, files in os.walk(base_dir):
            # Exclude unwanted directories in-place
            dirs[:] = [
                d for d in dirs
                if d not in excluded_dirs
                and not any(fnmatch.fnmatch(d, pattern) for pattern in excluded_dirs)
            ]

            for filename in files:
                # Skip non-Python files and excluded extensions
                if not filename.endswith(".py"):
                    continue

                if any(filename.endswith(ext) for ext in excluded_extensions):
                    continue

                full_path = os.path.join(root, filename)

                # Skip secret files, binary-related
                basename = os.path.basename(full_path)
                if basename.startswith(".") and basename.endswith((".key", ".pem", ".secret")):
                    continue

                rel_path = os.path.relpath(full_path, base_dir)
                discovered.append(rel_path)

        if not discovered:
            return "No Python source files found in the target project."

        # Sort for deterministic output
        discovered.sort()
        return "\n".join(discovered)

    except Exception as e:
        return f"Error listing project files: {e}"


def inspect_imports(file_path: str) -> str:
    """Use Python's ast module to parse imports and extract definitions.

    Args:
        file_path: Relative path from the project root to the .py file.

    Returns:
        String with imports, function definitions, class definitions,
        and other useful AST-derived information.
    """
    normalized = os.path.normpath(file_path)

    if normalized.startswith("..") or normalized.startswith("/") or normalized.startswith("\\"):
        return f"Error: Path traversal detected or absolute path: {file_path}"

    project_root = get_default_project_root()
    absolute_path = os.path.normpath(os.path.join(project_root, normalized))

    if not absolute_path.startswith(os.path.normpath(project_root) + os.sep) and \
       absolute_path != os.path.normpath(project_root):
        return f"Error: File outside allowed project root: {file_path}"

    if not normalized.endswith(".py"):
        return f"Error: Only .py files are allowed, got: {file_path}"

    try:
        with open(absolute_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except PermissionError:
        return f"Error: Permission denied reading: {file_path}"
    except UnicodeDecodeError:
        return f"Error: Cannot decode file (not UTF-8): {file_path}"
    except Exception as e:
        return f"Error reading file {file_path}: {e}"

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return f"Error: Invalid Python syntax in {file_path}: {e}"

    # Collect imports and definitions
    imports = []
    functions = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imp = alias.name
                line = getattr(alias, "lineno", None)
                if line:
                    imports.append(f"import {imp} (line {line})")
                else:
                    imports.append(f"import {imp}")

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                line = getattr(node, "lineno", None)
                if line:
                    imports.append(f"from {node.module} import ... (line {line})")
                else:
                    imports.append(f"from {node.module} import ...")

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            line = node.lineno
            args = []
            if node.args.args:
                args_names = [a.arg for a in node.args.args[:3]]
                args.append(", ".join(args_names))
                if len(node.args.args) > 3:
                    args.append("...")
            args_str = ", ".join(args) if args else "()"
            functions.append(f"def {node.name}({args_str}) at line {line}")

        elif isinstance(node, ast.ClassDef):
            line = node.lineno
            classes.append(f"class {node.name} at line {line}")

    # Sort by line number for deterministic output
    imports.sort(key=lambda x: int("".join(filter(str.isdigit, x)) or 0))
    functions.sort(key=lambda x: int("".join(filter(str.isdigit, x)) or 0))
    classes.sort(key=lambda x: int("".join(filter(str.isdigit, x)) or 0))

    output_parts = []

    if imports:
        output_parts.append("Imports:")
        for imp in imports:
            output_parts.append(f"  {imp}")

    if functions:
        output_parts.append("\nFunctions:")
        for func in functions:
            output_parts.append(f"  {func}")

    if classes:
        output_parts.append("\nClasses:")
        for cls in classes:
            output_parts.append(f"  {cls}")

    if not any([imports, functions, classes]):
        return f"No import/function/class definitions found in {file_path} (may be a minimal module)."

    return "\n".join(output_parts)


# ---------------------------------------------------------------------------
# Deterministic Graph Construction & Diagram Generation
# ---------------------------------------------------------------------------

def build_dependency_graph(
    project_root: Optional[str] = None,
    filter_pattern: Optional[str] = None,
) -> Dict[str, Any]:
    """Construct a deterministic dependency graph from Python AST analysis.

    Args:
        project_root: Root directory to analyze (defaults to target_project).
        filter_pattern: Optional substring filter for module or file names.

    Returns:
        Dictionary containing nodes, edges, modules, classes, and syntax errors.
    """
    root_dir = os.path.abspath(project_root or get_default_project_root())
    if not os.path.isdir(root_dir):
        return {
            "error": f"Project root directory not found: {root_dir}",
            "nodes": {},
            "edges": [],
            "syntax_errors": {},
        }

    excluded_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", "build", "dist", "node_modules"}

    discovered_files: List[str] = []
    for r, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in excluded_dirs and not d.startswith(".")]
        for f in files:
            if f.endswith(".py"):
                rel = os.path.relpath(os.path.join(r, f), root_dir).replace("\\", "/")
                discovered_files.append(rel)

    discovered_files.sort()

    nodes: Dict[str, Dict[str, Any]] = {}
    module_names: Set[str] = set()

    for rel_path in discovered_files:
        mod_name = os.path.splitext(rel_path)[0].replace("/", ".")
        if mod_name.endswith(".__init__"):
            mod_name = mod_name[:-9]
        elif mod_name == "__init__":
            mod_name = "root"
        module_names.add(mod_name)
        nodes[mod_name] = {
            "file": rel_path,
            "classes": [],
            "functions": [],
            "internal_imports": set(),
            "external_imports": set(),
        }

    syntax_errors: Dict[str, str] = {}
    edges_set: Set[Tuple[str, str, str]] = set()

    for mod_name, node_info in sorted(nodes.items()):
        full_path = os.path.join(root_dir, node_info["file"])
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as fp:
                code = fp.read()
            tree = ast.parse(code, filename=node_info["file"])
        except SyntaxError as e:
            syntax_errors[mod_name] = f"Line {e.lineno}: {e.msg}"
            continue
        except Exception as e:
            syntax_errors[mod_name] = str(e)
            continue

        for item in ast.walk(tree):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                node_info["functions"].append(item.name)
            elif isinstance(item, ast.ClassDef):
                node_info["classes"].append(item.name)
            elif isinstance(item, ast.Import):
                for alias in item.names:
                    imp_name = alias.name
                    target = _resolve_import_target(imp_name, module_names)
                    if target and target != mod_name:
                        node_info["internal_imports"].add(target)
                        edges_set.add((mod_name, target, "imports"))
                    else:
                        node_info["external_imports"].add(imp_name.split(".")[0])
            elif isinstance(item, ast.ImportFrom):
                if item.module:
                    mod_base = item.module
                    target = _resolve_import_target(mod_base, module_names)
                    if target and target != mod_name:
                        node_info["internal_imports"].add(target)
                        edges_set.add((mod_name, target, "imports"))
                    else:
                        node_info["external_imports"].add(mod_base.split(".")[0])

        node_info["functions"].sort()
        node_info["classes"].sort()
        node_info["internal_imports"] = sorted(list(node_info["internal_imports"]))
        node_info["external_imports"] = sorted(list(node_info["external_imports"]))

    # Convert edges to deterministic sorted list
    edges = [{"source": s, "target": t, "relation": r} for s, t, r in sorted(edges_set)]

    # Apply optional filter
    if filter_pattern:
        filter_lower = filter_pattern.lower()
        filtered_nodes = {
            k: v for k, v in nodes.items()
            if filter_lower in k.lower() or filter_lower in v["file"].lower()
        }
        filtered_node_names = set(filtered_nodes.keys())
        filtered_edges = [
            e for e in edges
            if e["source"] in filtered_node_names or e["target"] in filtered_node_names
        ]
        return {
            "project_root": root_dir,
            "nodes": filtered_nodes,
            "edges": filtered_edges,
            "syntax_errors": {k: v for k, v in syntax_errors.items() if k in filtered_node_names},
        }

    return {
        "project_root": root_dir,
        "nodes": nodes,
        "edges": edges,
        "syntax_errors": syntax_errors,
    }


def _resolve_import_target(imp_name: str, known_modules: Set[str]) -> Optional[str]:
    """Check if an import corresponds to an internal project module."""
    if imp_name in known_modules:
        return imp_name
    parts = imp_name.split(".")
    # Match longest prefix
    for i in range(len(parts) - 1, 0, -1):
        prefix = ".".join(parts[:i])
        if prefix in known_modules:
            return prefix
    return None


def sanitize_mermaid_id(identifier: str) -> str:
    """Sanitize identifier for safe Mermaid node IDs."""
    return identifier.replace(".", "_").replace("/", "_").replace("-", "_")


def generate_mermaid_diagram(
    graph: Dict[str, Any],
    diagram_type: str = "dependencies",
    impacted_modules: Optional[List[str]] = None,
) -> str:
    """Generate deterministic Mermaid diagram syntax from verified graph.

    Args:
        graph: Output of build_dependency_graph.
        diagram_type: One of 'dependencies', 'files', 'classes_functions', 'architecture', 'impact'.
        impacted_modules: List of module names to highlight in impact diagram.

    Returns:
        Valid Mermaid diagram definition string.
    """
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    impacted = set(impacted_modules or [])

    lines = ["graph TD"]

    if not nodes:
        lines.append("  empty[\"No modules discovered\"]")
        return "\n".join(lines)

    # 1. Output Nodes deterministically
    for mod_name in sorted(nodes.keys()):
        info = nodes[mod_name]
        node_id = sanitize_mermaid_id(mod_name)
        file_name = info["file"]

        if diagram_type == "classes_functions":
            funcs = ", ".join(info["functions"][:2])
            classes = ", ".join(info["classes"][:2])
            desc_parts = [file_name]
            if classes:
                desc_parts.append(f"class: {classes}")
            if funcs:
                desc_parts.append(f"fn: {funcs}")
            label = "\\n".join(desc_parts)
            lines.append(f'  {node_id}["{label}"]')
        elif diagram_type == "files":
            lines.append(f'  {node_id}["📄 {file_name}"]')
        else:
            lines.append(f'  {node_id}["{mod_name} ({file_name})"]')

    # 2. Output Edges deterministically
    for edge in edges:
        src = sanitize_mermaid_id(edge["source"])
        tgt = sanitize_mermaid_id(edge["target"])
        lines.append(f"  {src} --> {tgt}")

    # 3. Highlight impacted nodes if requested
    if diagram_type == "impact" or impacted:
        for mod_name in sorted(impacted):
            if mod_name in nodes:
                node_id = sanitize_mermaid_id(mod_name)
                lines.append(f"  style {node_id} fill:#ffebee,stroke:#c62828,stroke-width:2px")

    return "\n".join(lines)


def generate_drawio_xml(
    graph: Dict[str, Any],
    diagram_type: str = "dependencies",
    impacted_modules: Optional[List[str]] = None,
) -> str:
    """Generate valid draw.io XML (mxGraphModel format) deterministically.

    Args:
        graph: Output of build_dependency_graph.
        diagram_type: Diagram type string.
        impacted_modules: Modules to highlight.

    Returns:
        Valid XML string suitable for open_drawio_xml.
    """
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    impacted = set(impacted_modules or [])

    xml_lines = [
        '<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">',
        '  <root>',
        '    <mxCell id="0"/>',
        '    <mxCell id="1" parent="0"/>',
    ]

    cell_id = 2
    node_to_id: Dict[str, int] = {}

    # Deterministic layout in a clean grid
    col_width = 220
    row_height = 100
    cols_per_row = 3

    for idx, mod_name in enumerate(sorted(nodes.keys())):
        info = nodes[mod_name]
        col = idx % cols_per_row
        row = idx // cols_per_row
        x = 50 + col * col_width
        y = 50 + row * row_height

        label = f"{mod_name}\n({info['file']})"
        escaped_label = html.escape(label).replace("\n", "&#xa;")

        fill_color = "#e1f5fe"
        stroke_color = "#0288d1"
        if mod_name in impacted:
            fill_color = "#ffebee"
            stroke_color = "#c62828"

        style = f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill_color};strokeColor={stroke_color};fontFamily=Helvetica;fontSize=12;"

        xml_lines.append(
            f'    <mxCell id="{cell_id}" value="{escaped_label}" style="{style}" vertex="1" parent="1">'
        )
        xml_lines.append(
            f'      <mxGeometry x="{x}" y="{y}" width="180" height="60" as="geometry"/>'
        )
        xml_lines.append('    </mxCell>')

        node_to_id[mod_name] = cell_id
        cell_id += 1

    for edge in edges:
        src = edge["source"]
        tgt = edge["target"]
        if src in node_to_id and tgt in node_to_id:
            src_id = node_to_id[src]
            tgt_id = node_to_id[tgt]
            edge_style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#455a64;strokeWidth=1.5;"
            xml_lines.append(
                f'    <mxCell id="{cell_id}" style="{edge_style}" edge="1" parent="1" source="{src_id}" target="{tgt_id}">'
            )
            xml_lines.append('      <mxGeometry relative="1" as="geometry"/>')
            xml_lines.append('    </mxCell>')
            cell_id += 1

    xml_lines.append('  </root>')
    xml_lines.append('</mxGraphModel>')

    return "\n".join(xml_lines)


def generate_architecture_report(
    graph: Dict[str, Any],
    diagram_url: Optional[str] = None,
    mcp_error: Optional[str] = None,
    mermaid_code: Optional[str] = None,
    diagram_type: str = "dependencies",
    impacted_modules: Optional[List[str]] = None,
) -> str:
    """Format structured, verified architecture report without AI guessing.

    Args:
        graph: Dependency graph from build_dependency_graph.
        diagram_url: Verified draw.io diagram URL if MCP succeeded.
        mcp_error: Error message if MCP failed or was unreachable.
        mermaid_code: Generated Mermaid syntax for offline rendering.
        diagram_type: Diagram type requested.
        impacted_modules: List of impacted modules if applicable.

    Returns:
        Structured Markdown report.
    """
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    syntax_errors = graph.get("syntax_errors", {})

    lines = [
        "## Verified Architecture Report",
        "*Generated deterministically via Python AST & Static Analysis — No LLM Inference*",
        "",
        "### 1. Architecture Overview",
        f"- **Analyzed Project Directory**: `{graph.get('project_root', 'target_project')}`",
        f"- **Discovered Python Modules**: {len(nodes)}",
        f"- **Verified Internal Dependencies (Edges)**: {len(edges)}",
        f"- **Diagram Type**: `{diagram_type}`",
        "",
    ]

    # Important Files
    lines.append("### 2. Verified Modules & Files")
    if nodes:
        for mod, info in sorted(nodes.items()):
            classes_str = f", classes: {len(info['classes'])}" if info["classes"] else ""
            funcs_str = f", functions: {len(info['functions'])}" if info["functions"] else ""
            lines.append(f"- **`{mod}`** (`{info['file']}`){classes_str}{funcs_str}")
    else:
        lines.append("- *No Python source files discovered in target project.*")
    lines.append("")

    # Import Relationships
    lines.append("### 3. Key Import Relationships")
    if edges:
        for edge in edges:
            lines.append(f"- `{edge['source']}` ➔ `{edge['target']}`")
    else:
        lines.append("- *No internal cross-module dependencies detected.*")
    lines.append("")

    # Syntax Errors
    if syntax_errors:
        lines.append("### 4. Syntax & Parsing Warnings")
        for mod, err in sorted(syntax_errors.items()):
            lines.append(f"- ⚠️ **`{mod}`**: {err}")
        lines.append("")

    # Draw.io MCP Integration Status & URL
    lines.append("### 5. Diagram Status & Draw.io MCP Result")
    if diagram_url:
        lines.append(f"✅ **Interactive Draw.io Diagram Generated Successfully!**")
        lines.append(f"- **Diagram URL**: [{diagram_url}]({diagram_url})")
        lines.append("- You can click the link above to view, pan, zoom, or edit the diagram in Draw.io.")
    elif mcp_error:
        lines.append(f"⚠️ **Draw.io MCP Diagram Service Unavailable**: {mcp_error}")
        lines.append("- The Architecture Mapper successfully analyzed the codebase and produced the Mermaid diagram below.")
        lines.append("- *Note: To open directly in Draw.io, verify that `@drawio/mcp` is running via `npx -y @drawio/mcp`.*")
    else:
        lines.append("- Diagram generation was not requested or draw.io MCP was not invoked.")
    lines.append("")

    # Mermaid diagram code block
    if mermaid_code:
        lines.append("### 6. Mermaid Architecture Definition")
        lines.append("```mermaid")
        lines.append(mermaid_code)
        lines.append("```")
        lines.append("")

    # Limitations of Static Analysis
    lines.append("### 7. Limitations of Static Analysis")
    lines.append("- **Dynamic Imports**: Imports performed dynamically via `importlib` or `__import__` are not statically captured.")
    lines.append("- **Conditional & Late Imports**: Imports nested conditionally within `if` blocks or inside functions are captured structurally but may not execute at runtime.")
    lines.append("- **Runtime Monkey Patching**: Dynamic method injection or runtime attribute modifications cannot be verified through AST alone.")

    return "\n".join(lines)