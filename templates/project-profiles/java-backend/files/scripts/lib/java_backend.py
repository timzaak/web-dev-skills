from pathlib import Path

from .cli import require_executable


def backend_dir(repo_root: Path) -> Path:
    nested = repo_root / "backend"
    if (nested / "pom.xml").is_file():
        return nested
    if (repo_root / "pom.xml").is_file():
        return repo_root
    return nested


def detect_build_tool(root: Path) -> str:
    if (root / "pom.xml").is_file():
        return "maven"
    raise RuntimeError("Backend changes detected, but no Maven build file was found in backend/.")


def maven_command(root: Path, goals: list[str]) -> list[str]:
    return [require_executable("mvn", "mvn.cmd"), *goals]


def build_test_command(root: Path, extra_args: list[str] | None = None) -> list[str]:
    extra_args = extra_args or []
    detect_build_tool(root)
    return maven_command(root, ["test", *extra_args])


def build_quality_commands(root: Path) -> list[list[str]]:
    detect_build_tool(root)
    commands: list[list[str]] = []
    format_check = build_format_check_command(root)
    if format_check is not None:
        commands.append(format_check)
    if (root / "pom.xml").is_file():
        commands.append(maven_command(root, ["verify", "-DskipTests"]))
    return commands


def build_format_check_command(root: Path) -> list[str] | None:
    tool = detect_build_tool(root)
    if tool == "maven":
        pom = root / "pom.xml"
        if pom.is_file():
            text = pom.read_text(encoding="utf-8", errors="ignore")
            if "spotless-maven-plugin" in text:
                return maven_command(root, ["spotless:check"])
            if "maven-checkstyle-plugin" in text:
                return maven_command(root, ["checkstyle:check"])
        return None

    return None


def build_run_command(root: Path) -> list[str]:
    detect_build_tool(root)
    return maven_command(root, ["spring-boot:run"])
