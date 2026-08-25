import { chromium } from "playwright";
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 1 });
const url = process.argv[2] || "http://localhost:5173/";
await p.goto(url, { waitUntil: "networkidle" });
await p.waitForTimeout(6000);
// How much of the canvas is non-white? Blank map == ~0
const ink = await p.evaluate(() => {
  const c = document.querySelector("canvas");
  const gl = c.getContext("webgl2") || c.getContext("webgl");
  const w = 200, h = 150;
  const px = new Uint8Array(w * h * 4);
  gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
  let coloured = 0;
  for (let i = 0; i < px.length; i += 4) {
    if (px[i] !== 0 || px[i+1] !== 0 || px[i+2] !== 0) coloured++;
  }
  return { sampled: w * h, nonBlack: coloured };
});
console.log("canvas pixels:", JSON.stringify(ink));
await p.screenshot({ path: process.argv[3] || "/tmp/app.png" });
await b.close();
