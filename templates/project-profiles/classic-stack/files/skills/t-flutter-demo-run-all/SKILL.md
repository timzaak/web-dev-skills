---
name: t-flutter-demo-run-all
description: Run all Android Patrol user-story demo files with resumable checkpoints.
argument-hint: "[continue] [--device <android-id>]"
allowed-tools: [Read, Glob, Grep, Bash, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, Agent]
---

# Flutter Demo Run All

使用目标项目或插件的 `scripts/flutter-demo-run-all.py discover [continue]` 发现 `patrol_test/**/*_test.dart` 并持久化批次。

- 按发现顺序串行调用 `/t-tools:t-flutter-demo-run` 的整文件修复闭环。
- 每个文件前写 checkpoint，完成后 record；中断后用 `continue` 从首个未完成文件恢复。
- 同一批次固定 Android device；设备或环境阻塞时保留 checkpoint，不跳过文件。
- 完成后 finalize；首版不提供 Playwright scan/cluster 模式。

