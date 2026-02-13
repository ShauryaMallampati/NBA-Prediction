import next from "eslint-config-next/core-web-vitals"

export default [
  { ignores: [".venv/**", "data/**", "artifacts/**", "dist/**"] },
  ...next,
]
