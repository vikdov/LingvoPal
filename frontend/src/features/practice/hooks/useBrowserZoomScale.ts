import { useState, useEffect } from 'react';

// outerWidth is in device-independent pixels (not affected by CSS zoom).
// innerWidth is in CSS pixels (shrinks when user zooms in).
// Their ratio ≈ browser zoom factor, independent of retina DPR.
// scale = 1/zoomFactor → multiply fixed-size values by this to keep them zoom-invariant.
function getScale(): number {
  const ratio = window.outerWidth / window.innerWidth;
  return ratio > 0.1 ? 1 / ratio : 1;
}

export function useBrowserZoomScale(): number {
  const [scale, setScale] = useState(getScale);
  useEffect(() => {
    const update = () => setScale(getScale());
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);
  return scale;
}
