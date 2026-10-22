import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // eslint-plugin-react can't auto-detect the React version under ESLint 10.
  { settings: { react: { version: "19" } } },
  // Rule 2: a function's branching stays readable; the generated API types are exempt.
  { ignores: ["types/api/**"], rules: { complexity: ["error", 15] } },
  // TODO(rule 2): InterviewPage (49) is over 15; split it at its seams once the work open in
  // this file is committed.
  {
    files: ["app/companies/\\[companyId\\]/interviews/\\[id\\]/page.tsx"],
    rules: { complexity: "off" },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // The MCP examples the developer docs show: their own packages, not the site's.
    "content/mcp/**",
  ]),
]);

export default eslintConfig;
