// Touch input is an observer camera only; it sends Crow no behavioural commands.
export function normaliseStick(dx, dy, radius = 42) {
  const distance = Math.hypot(dx, dy), scale = distance > radius ? radius / distance : 1;
  return { right: dx * scale / radius, forward: dy === 0 ? 0 : -dy * scale / radius,
    x: dx * scale, y: dy * scale };
}

export function installTouchControls({ canvas, pad, knob, onLook }) {
  const input = { forward: 0, right: 0 };
  let stickPointer = null, lookPointer = null, lastX = 0, lastY = 0;
  function reset() { input.forward = input.right = 0; stickPointer = lookPointer = null; knob.style.transform = 'translate(0px,0px)'; }
  function update(e) {
    const rect = pad.getBoundingClientRect();
    const v = normaliseStick(e.clientX - rect.left - rect.width / 2, e.clientY - rect.top - rect.height / 2);
    input.right = Math.abs(v.right) > .12 ? v.right : 0;
    input.forward = Math.abs(v.forward) > .12 ? v.forward : 0;
    knob.style.transform = `translate(${v.x}px,${v.y}px)`;
  }
  pad.addEventListener('pointerdown', e => { if (stickPointer !== null) return; e.preventDefault(); stickPointer = e.pointerId; pad.setPointerCapture(e.pointerId); update(e); });
  pad.addEventListener('pointermove', e => { if (e.pointerId === stickPointer) { e.preventDefault(); update(e); } });
  for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) pad.addEventListener(name, e => { if (e.pointerId === stickPointer) { input.forward = input.right = 0; stickPointer = null; knob.style.transform = 'translate(0px,0px)'; } });
  canvas.addEventListener('pointerdown', e => { if (e.pointerType === 'mouse' || lookPointer !== null) return; e.preventDefault(); lookPointer = e.pointerId; lastX = e.clientX; lastY = e.clientY; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener('pointermove', e => { if (e.pointerId !== lookPointer) return; onLook((e.clientX - lastX) * .004, (e.clientY - lastY) * .004); lastX = e.clientX; lastY = e.clientY; });
  for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) canvas.addEventListener(name, e => { if (e.pointerId === lookPointer) lookPointer = null; });
  globalThis.addEventListener('blur', reset);
  document.addEventListener('visibilitychange', () => { if (document.hidden) reset(); });
  return input;
}
