import { defineConfig } from 'tsup';

export default defineConfig({
  entry: {
    cli: 'src/cli.ts',
    server: 'src/server.ts',
    index: 'src/index.ts'
  },
  format: ['esm'],
  dts: true,
  clean: true,
  minify: false, // Disable minification to avoid shebang issues
  target: 'node18',
  splitting: false,
  sourcemap: true,
  treeshake: true,
  define: {
    'import.meta.url': 'import.meta.url'
  },
  onSuccess: 'echo "✅ Build completed successfully!"'
});