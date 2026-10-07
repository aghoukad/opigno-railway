import { build } from 'esbuild';
await build({
  entryPoints: ['editor.js'],
  outfile: 'dist/ckeditor.js',
  bundle: true,
  minify: true,
  format: 'iife',
  target: ['es2022'],
  loader: { '.css': 'text' },
  legalComments: 'inline',
});
