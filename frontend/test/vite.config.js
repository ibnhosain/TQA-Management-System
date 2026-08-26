import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));

/* পরীক্ষার বিল্ড — কেবল `npm run test:ui` চালালে ব্যবহার হয়।
   চালু সাইটের বিল্ড (npm run build) এই ফাইলটি ছোঁয়ও না। */
export default defineConfig({
  root: path.resolve(here, ".."),
  plugins: [react()],
  resolve: {
    alias: [
      // সার্ভারে না গিয়ে নকল তথ্য দিয়ে চালানোর জন্য
      { find: /^\.\/api$/, replacement: path.resolve(here, "api-stub.js") },
    ],
  },
});
