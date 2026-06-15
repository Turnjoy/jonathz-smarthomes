function paintCameraPlaceholder(canvas) {
  const context = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  const gradient = context.createLinearGradient(0, 0, width, height);
  gradient.addColorStop(0, '#0f172a');
  gradient.addColorStop(1, '#1f2937');
  context.fillStyle = gradient;
  context.fillRect(0, 0, width, height);
  context.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--brand-accent') || '#f59e0b';
  context.lineWidth = 6;
  context.strokeRect(28, 28, width - 56, height - 56);
  context.fillStyle = '#e2e8f0';
  context.font = '24px system-ui, sans-serif';
  context.textAlign = 'center';
  context.fillText('Camera stream not configured', width / 2, height / 2);
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.camera-frame canvas').forEach(paintCameraPlaceholder);
});
