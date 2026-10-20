import { defineConfig, loadEnv } from "vite";

// The page's Content-Security-Policy allows network calls only to this origin
// and to the API origin named by VITE_API_URL (absent in a guest-only build).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  const apiOrigin = env.VITE_API_URL ? new URL(env.VITE_API_URL).origin : "";
  return {
    plugins: [{ name: "csp-api-origin", transformIndexHtml: html => html.replace("__API_ORIGIN__", apiOrigin).replace("'self' ;", "'self';") }],
    build: { sourcemap: false },
  };
});
