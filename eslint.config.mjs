import js from "@eslint/js";
import globals from "globals";
import { defineConfig, globalIgnores } from "eslint/config";

const configFile = [
  "./vite.config.mjs"
];
const assetFiles = [
  "./assets/js/*.{js,mjs,cjs}",
  "./vite-src/*.{js,mjs,cjs}"
];
const allFiles = [
  "./assets/js/*.{js,mjs,cjs}",
  "./vite-src/*.{js,mjs,cjs}",
  "./vite.config.mjs"
];

export default defineConfig([
  globalIgnores(["./assets/js/editor-old.js"]),
  { files: allFiles, plugins: { js }, extends: ["js/recommended"] },
  { files: assetFiles, languageOptions: { globals: {...globals.browser} } },
  { files: configFile, languageOptions: { globals: {...globals.node} } },
]);
