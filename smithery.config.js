export default {
  esbuild: {
    // Mark packages with native dependencies as external
    external: [
      // MCP SDK and related packages should be bundled
      // Add any problematic packages here if build fails
    ],

    // Enable minification for production
    minify: true,

    // Set Node.js target version
    target: "node18",

    // Bundle format
    format: "esm",

    // Include source maps for debugging
    sourcemap: true,

    // Platform-specific optimizations
    platform: "node"
  }
}