"""Regression tests for the real Tree-sitter Java analyzer.

Locks in the fix for the javaparser bug: `javaparser` doesn't exist on PyPI,
so JAVA_AVAILABLE used to be permanently False and Java repos (e.g. the
springboot_app demo) always produced empty metrics. tree-sitter-java replaces
it, and the JavaFileMetrics/JavaFunctionMetrics/JavaClassMetrics dataclasses
intentionally mirror architect_insight/metrics/complexity.py's FileMetrics/
FunctionMetrics/ClassMetrics shape (field names included) so
patterns.py::detect_anti_patterns works on them unmodified.
"""

from architect_insight.analyzers.java_analyzer import JAVA_AVAILABLE, analyze_java_directory
from architect_insight.metrics.patterns import detect_anti_patterns


def test_java_available():
    # Regression guard: this used to always be False (javaparser isn't a real package).
    assert JAVA_AVAILABLE is True


def test_detects_god_class(tmp_path):
    methods = "\n".join(f"    public void method{i}() {{ int x = {i}; }}" for i in range(16))
    (tmp_path / "GodClass.java").write_text(f"public class GodClass {{\n{methods}\n}}\n")

    result = analyze_java_directory(str(tmp_path))

    assert result["files_analyzed"] == 1
    assert result["total_classes"] == 1
    assert result["total_methods"] == 16
    assert result["has_java_analysis"] is True
    assert result["file_errors"] == 0

    findings = detect_anti_patterns(result["files"][0])
    assert any(f.type == "God Class" for f in findings)


def test_detects_long_method_with_real_complexity(tmp_path):
    branches = "\n".join(f"        if (a > {i}) {{ System.out.println({i}); }}" for i in range(15))
    (tmp_path / "Complex.java").write_text(
        f"public class Complex {{\n    public int bar(int a, int b, int c) {{\n{branches}\n        return a;\n    }}\n}}\n"
    )

    result = analyze_java_directory(str(tmp_path))
    fn = result["files"][0].functions[0]

    assert fn.qualified_name == "Complex.bar"
    assert fn.complexity == 16  # 1 base + 15 if-statements
    assert fn.num_params == 3

    findings = detect_anti_patterns(result["files"][0])
    assert any(f.type == "Long Method" for f in findings)


def test_files_key_is_stripped_before_reaching_collector_output(tmp_path):
    """collector.py pops "files" (raw dataclasses, not JSON-serializable) before
    including java_analysis in the final report — verified at the collector level
    in test_collector_debt_map.py; here we just confirm files/ Java detection works
    on a real, minimal repo so that regression is meaningful."""
    (tmp_path / "Empty.java").write_text("public class Empty {}\n")
    result = analyze_java_directory(str(tmp_path))
    assert result["files_analyzed"] == 1
    assert result["files"][0].parse_error is None
