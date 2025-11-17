import '@zmd-lib/katex/dist/katex.min.css';
import.meta.glob('@zmd-lib/katex/dist/fonts/*', {
  eager: true, // This ensures that all images are imported eagerly (without waiting)
});
