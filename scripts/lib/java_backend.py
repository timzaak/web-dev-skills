import os
from pathlib import Path

from .cli import require_executable


def backend_dir(repo_root: Path) -> Path:
    return repo_root / "backend"


def _script_path(path: Path) -> str:
    if os.name == "nt" and path.with_suffix(path.suffix + ".cmd").is_file():
        return str(path.with_suffix(path.suffix + ".cmd"))
    return str(path)


def detect_build_tool(root: Path) -> str:
    if (root / "mvnw").is_file() or (root / "mvnw.cmd").is_file() or (root / "pom.xml").is_file():
        return "maven"
    if (
        (root / "gradlew").is_file()
        or (root / "gradlew.bat").is_file()
        or (root / "build.gradle").is_file()
        or (root / "build.gradle.kts").is_file()
    ):
        return "gradle"
    raise RuntimeError("Backend changes detected, but no Maven or Gradle build file was found in backend/.")


def maven_command(root: Path, goals: list[str]) -> list[str]:
    if os.name == "nt" and (root / "mvnw.cmd").is_file():
        return [str(root / "mvnw.cmd"), *goals]
    if (root / "mvnw").is_file():
        return [_script_path(root / "mvnw"), *goals]
    return [require_executable("mvn", "mvn.cmd"), *goals]


def gradle_command(root: Path, tasks: list[str]) -> list[str]:
    if os.name == "nt" and (root / "gradlew.bat").is_file():
        return [str(root / "gradlew.bat"), *tasks]
    if (root / "gradlew").is_file():
        return [_script_path(root / "gradlew"), *tasks]
    return [require_executable("gradle", "gradle.bat"), *tasks]


def build_test_command(root: Path, extra_args: list[str] | None = None) -> list[str]:
    extra_args = extra_args or []
    tool = detect_build_tool(root)
    if tool == "maven":
        return maven_command(root, ["test", *extra_args])
    return gradle_command(root, ["test", *extra_args])


def build_quality_commands(root: Path) -> list[list[str]]:
    tool = detect_build_tool(root)
    if tool == "maven":
        commands = [maven_command(root, ["test"])]
        if (root / "pom.xml").is_file():
            commands.append(maven_command(root, ["verify", "-DskipTests"]))
        return commands
    return [gradle_command(root, ["test"]), gradle_command(root, ["check"])]


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

    build_files = [root / "build.gradle", root / "build.gradle.kts"]
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in build_files if path.is_file())
    if "spotless" in text:
        return gradle_command(root, ["spotlessCheck"])
    if "checkstyle" in text:
        return gradle_command(root, ["checkstyleMain"])
    return None


def build_run_command(root: Path) -> list[str]:
    tool = detect_build_tool(root)
    if tool == "maven":
        return maven_command(root, ["spring-boot:run"])
    return gradle_command(root, ["bootRun"])
