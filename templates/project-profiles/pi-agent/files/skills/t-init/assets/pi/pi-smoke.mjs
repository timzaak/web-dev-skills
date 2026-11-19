import { mkdtemp, mkdir, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
let scratch;
try {
  if (process.argv.length > 3) throw new Error("Usage: node scripts/pi-smoke.mjs [resource-root]");
  const resourceRoot = resolve(projectRoot, process.argv[2] ?? ".");
  if (!(await stat(resourceRoot)).isDirectory()) throw new Error("Resource root must be a local directory");
  const { DefaultResourceLoader, SettingsManager } = await import("@earendil-works/pi-coding-agent");
  scratch = await mkdtemp(join(resolve(tmpdir()), "pi-init-smoke-"));
  const cwd = join(scratch, "cwd");
  await mkdir(cwd);
  // 隔离发现和配置，只显式加载本次资源，不启动会话或请求模型。
  const loader = new DefaultResourceLoader({
    cwd,
    agentDir: join(scratch, "agent"),
    settingsManager: SettingsManager.inMemory({ packages: [] }),
    additionalExtensionPaths: [resourceRoot],
    noExtensions: true,
    noSkills: true,
    noPromptTemplates: true,
    noThemes: true,
    noContextFiles: true,
  });
  await loader.reload();
  const extensions = loader.getExtensions();
  const skills = loader.getSkills();
  const prompts = loader.getPrompts();
  const themes = loader.getThemes();
  const diagnostics = [
    ...extensions.errors,
    ...(extensions.warnings ?? []),
    ...skills.diagnostics,
    ...prompts.diagnostics,
    ...themes.diagnostics,
  ];
  const count = extensions.extensions.length + skills.skills.length + prompts.prompts.length + themes.themes.length;
  const passed = diagnostics.length === 0 && count > 0;
  console.log(JSON.stringify({
    status: passed ? "passed" : "failed",
    resourceRoot,
    extensions: extensions.extensions.map((entry) => entry.resolvedPath),
    skills: skills.skills.map((entry) => entry.name),
    prompts: prompts.prompts.map((entry) => entry.name),
    themes: themes.themes.map((entry) => entry.name),
    diagnostics,
    ...(count === 0 ? { reason: "No resources discovered" } : {}),
    modelCalls: "not_verified",
    sessionLifecycle: "not_verified",
  }));
  if (!passed) process.exitCode = 1;
} catch (error) {
  console.error(JSON.stringify({ status: "failed", error: String(error), modelCalls: "not_verified", sessionLifecycle: "not_verified" }));
  process.exitCode = 1;
} finally {
  if (scratch) {
    if (dirname(scratch) !== resolve(tmpdir())) throw new Error("Unexpected smoke scratch path");
    await rm(scratch, { recursive: true, force: true });
  }
}
