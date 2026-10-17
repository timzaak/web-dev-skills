# Taro Builder Rules

- This project targets WeChat mini-program development through Taro and React.
- The canonical technical baseline is `${CLAUDE_PLUGIN_ROOT}/guides/miniapp/constitution.md`.
- Keep all app source files inside `src/`.
- Add pages under `src/pages/<page>/index.tsx` and register them in `src/app.config.ts`.
- Prefer `@taroify/core` components for mobile UI primitives before introducing custom wrappers.
- Use Tailwind utility classes only for layout and composition speed. Tailwind is not the theme source of truth.
- Tokens under `tokens/*.json` are the only design source of truth. They are compiled by Style Dictionary into `src/theme/`.
- Tokens Studio is an input source only. Runtime code must consume compiled outputs from `src/theme/`.
- Radix Colors and Open Props may inform token values, but never appear as scattered runtime literals.
- Use the shared `AppIcon` wrapper for every icon. Do not import `@taroify/icons`, Iconify runtime packages, or ad-hoc SVG components directly in business pages.
- Do not introduce `React Router`, `Next.js`, `framer-motion`, `next-themes`, shadcn/ui, or browser-only entrypoints.
- Preserve `config/index.js`, `src/app.config.ts`, `package.json`, `project.config.json`, `tailwind.config.ts`, `style-dictionary.config.mjs`, and `tokens/*.json` unless the user explicitly asks for infrastructure changes.
