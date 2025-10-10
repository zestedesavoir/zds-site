import { defineConfig, globalIgnores } from "eslint/config";
import jsdoc from "eslint-plugin-jsdoc";
import globals from "globals";
import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all
});

export default defineConfig([globalIgnores(["assets/js/editor-old.js"]), {
    extends: compat.extends("standard"),

    plugins: {
        jsdoc,
    },

    languageOptions: {
        globals: {
            ...globals.browser,
            ...globals.node,
            ...globals.jquery,
        },
    },

    rules: {
        "object-shorthand": "off",
        "no-multiple-empty-lines": "off",
        "space-before-function-paren": ["error", "never"],
        "jsdoc/check-alignment": "error",
    },
}]);
