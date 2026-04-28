# Taro + Taroify + Tailwind CSS + weapp-tailwindcss Constitution

## 1. Technical line positioning

- Target platforms: `weapp` first, `h5` second.
- Platform role: this is the official React-oriented fallback/secondary line.
- Typical use cases: teams with React background, migration from existing React mobile/web code, cases that benefit from Taro ecosystem familiarity.
- Why this line exists: some teams need React mental models and Taro runtime while still staying within mini-program constraints.
- Relationship to the main line: this line is official, but it is not the primary quality baseline. The uni-app line remains the default first-class path.

## 2. Stack list

- `Taro`
- `React`
- `TypeScript`
- `Taroify`
- `Tailwind CSS`
- `weapp-tailwindcss`
- `Style Dictionary`
- `Tokens Studio`
- `@tokens-studio/sd-transforms`
- `Iconify`
- `Radix Colors`
- `Open Props`

## 3. Directory and file responsibilities

Stable skeleton:

- `src/app.tsx`: app bootstrap
- `src/app.config.ts`: page registration source
- `src/pages/`: page entry files
- `config/`: Taro build config
- `src/theme/`: compiled token outputs, theme CSS, icon manifest, Taroify mapping
- `src/styles/`: Tailwind entry and shared styles
- `tokens/`: token source truth
- `scripts/`: token and icon build scripts
- `tailwind.config.ts`: Tailwind productivity config only
- `style-dictionary.config.mjs`: official token compiler config
- `template.config.json`: template metadata contract for builder/runtime/validator

AI-editable areas:

- `src/pages/**`
- `src/components/**`
- `src/store/**` if introduced
- `src/services/**` or `src/utils/**`

Protected-file candidates:

- `config/index.js`
- `src/app.config.ts`
- `package.json`
- `tailwind.config.ts`
- `project.config.json`
- `style-dictionary.config.mjs`
- `tokens/base.json`
- `tokens/light.json`
- `tokens/dark.json`
- `tokens/brand-default.json`
- `scripts/build-icons.mjs`
- `src/theme/taroify-theme.ts`
- `src/theme/icons/manifest.ts`
- `template.config.json`

## 4. Theme system constitution

- Tokens are the only theme source of truth.
- Tailwind classes are not the theme source.
- `tailwind.config.ts` must only map to token-backed CSS variables.
- `Style Dictionary` is the only official token compiler.
- `Tokens Studio` is a design input layer only.
- `Radix Colors` is a reference palette only and must be absorbed into platform tokens.
- `Open Props` is a reference source only for spacing/radius/shadow/motion and must be absorbed into platform tokens.
- Reference values from those upstream libraries are already embedded in `tokens/*.json` source files; platform token source files remain curated and authoritative.
- `Taroify` theme config and Tailwind utilities must both consume mapped platform tokens.
- Runtime code consumes compiled outputs from `src/theme/`, not raw design-source metadata.

## 5. Icon constitution

- Official icon source: `Iconify`.
- Official icon runtime strategy: prebuilt local SVG assets plus generated manifest.
- Official component entry: `src/components/AppIcon.tsx`.
- Runtime pages and components must use `AppIcon`.
- Icons are generated offline by `scripts/build-icons.mjs`.
- Do not mix `@taroify/icons`, `lucide-react`, or any additional icon runtime library into business code.

## 6. Styling rules

- Tailwind CSS and `weapp-tailwindcss` are allowed for layout and composition.
- Colors, spacing, radius, shadow, and motion values must resolve back to token-backed variables.
- Do not put the real theme definition inside `tailwind.config.ts`.
- `Taroify` theme mapping must read token-backed values.
- Tailwind arbitrary values are acceptable only when they reference token-backed CSS variables.
- Radix Colors may influence palette token values after they are converted to platform tokens.
- Open Props may influence spacing/radius/shadow/motion token values after they are converted to platform tokens.
- Direct scattered use of Radix/Open Props values is forbidden.

## 7. Builder constraints

- Do not break `config/index.js`, `src/app.config.ts`, `style-dictionary.config.mjs`, `scripts/build-icons.mjs`, or `template.config.json`.
- New pages must be created under `src/pages/<name>/index.tsx` and registered in `src/app.config.ts`.
- Prefer `Taroify` primitives before inventing new core controls.
- Do not introduce `react-router-dom`, `next-themes`, `framer-motion`, `shadcn/ui`, `@radix-ui/react-*`, or browser-only React libraries.
- Theme edits must start from `tokens/*.json`.
- Icons must use `AppIcon`.

## 8. Diagnostics and repair contract

Typecheck must validate:

- React + TypeScript correctness
- token and icon imports
- Taro page/component correctness

Template integrity must validate:

- required files exist
- token outputs exist
- icon manifest exists
- required page routes are registered in `src/app.config.ts`
- forbidden imports and dependencies are absent

Build must validate:

- `taro build --type weapp`
- `taro build --type h5` when previewing

Preview health must validate:

- the H5 preview is no longer on untouched starter content
- no visible build-error overlay
- compiled theme outputs are present

Priority auto-fix classes:

- missing page registration
- missing token outputs
- broken icon imports
- theme import drift
- safe Taro config drift

## 9. Prohibited actions

- Do not let Tailwind become the theme source of truth.
- Do not import `@taroify/icons`, `lucide-react`, `react-router-dom`, `next-themes`, `framer-motion`, `@radix-ui/react-*`, or web-only React builder packages.
- Do not write direct color literals when platform tokens already exist.
- Do not bypass `AppIcon`.
- Do not create a second theme system parallel to Style Dictionary.
