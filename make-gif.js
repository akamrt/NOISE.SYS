// Pure Node.js GIF maker - no external dependencies
// Writes valid GIF89a with LZW compression

const fs = require('fs');

function writeGIF(filename, width, height, frames, delay = 10) {
  // frames: array of { pixels: Buffer (RGB) }
  const fp = fs.createWriteStream(filename);
  
  // Header
  fp.write('GIF89a');
  fp.write(le16(width));
  fp.write(le16(height));
  fp.write(Int8Array.from([0xF7, 0x00, 0x00])); // GCT follows, 256 colors
  fp.write(Int8Array.from([0])); // background color index
  fp.write(Int8Array.from([0])); // pixel aspect ratio

  // Global Color Table (256 RGB entries)
  const gct = [];
  for (let i = 0; i < 256; i++) {
    const g = Math.floor(92 + 163 * (i / 255));
    const c = Math.min(255, g);
    gct.push(c, g, c); // RGB - green-ish palette
  }
  fp.write(Buffer.from(gct));

  // Netscape extension for looping
  fp.write(Buffer.from([0x21, 0xFF, 0x0B]));
  fp.write(Buffer.from('NETSCAPE2.0'));
  fp.write(Buffer.from([0x03, 0x01]));
  fp.write(le16(0)); // loop forever
  fp.write(Buffer.from([0x00]));

  for (const frame of frames) {
    const pixels = frame.pixels;
    
    // Graphic Control Extension
    fp.write(Buffer.from([0x21, 0xF9, 0x04]));
    fp.write(Buffer.from([0x00])); // no transparency
    fp.write(le16(delay)); // delay in 1/100s
    fp.write(le16(0)); // transparent color index
    fp.write(Buffer.from([0x00]));

    // Image Descriptor
    fp.write(Buffer.from([0x2C]));
    fp.write(le16(0)); // left
    fp.write(le16(0)); // top
    fp.write(le16(width));
    fp.write(le16(height));
    fp.write(Buffer.from([0x00])); // no local color table

    // LZW encode
    const minCodeSize = Buffer.from([8]);
    const lzwData = lzwEncode(pixels, 8);
    
    fp.write(minCodeSize);
    let offset = 0;
    const subBlockSize = 255;
    while (offset < lzwData.length) {
      const chunk = lzwData.slice(offset, offset + subBlockSize);
      fp.write(Int8Array.from([chunk.length]));
      fp.write(chunk);
      offset += subBlockSize;
    }
    fp.write(Int8Array.from([0])); // block terminator
  }

  fp.write(Buffer.from([0x3B])); // trailer
  fp.end();
}

function lzwEncode(pixels, minCodeSize) {
  const clearCode = 1 << minCodeSize;
  const eoiCode = clearCode + 1;
  let codeSize = minCodeSize + 1;
  let nextCode = eoiCode + 1;
  const maxCode = 4096;

  const dict = new Map();
  for (let i = 0; i < clearCode; i++) dict.set(String.fromCharCode(i), i);

  const output = [];
  let bits = 0;
  let bitCount = 0;

  function writeCode(code) {
    bits |= code << bitCount;
    bitCount += codeSize;
    while (bitCount >= 8) {
      output.push(bits & 0xFF);
      bits >>= 8;
      bitCount -= 8;
    }
  }

  writeCode(clearCode);
  let prefix = '';

  for (let i = 0; i < pixels.length; i += 3) {
    const k = String.fromCharCode(pixels[i]); // R (use R as index)
    const combined = prefix + k;

    if (dict.has(combined)) {
      prefix = combined;
    } else {
      writeCode(dict.get(prefix));
      if (nextCode < maxCode) {
        dict.set(combined, nextCode++);
        if (nextCode > (1 << codeSize) && codeSize < 12) codeSize++;
      }
      prefix = k;
    }
  }

  if (prefix) writeCode(dict.get(prefix));
  writeCode(eoiCode);

  if (bitCount > 0) output.push(bits & 0xFF);
  return Buffer.from(output);
}

function le16(n) {
  return Int8Array.from([n & 0xFF, (n >> 8) & 0xFF]);
}

// Generate oscilloscope animation frame
function makeFrame(t, w, h) {
  const buf = Buffer.alloc(w * h * 3);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const idx = (y * w + x) * 3;
      const cx = x / w;
      const cy = 0.5 + 0.35 * Math.sin(cx * Math.PI * 6 + t);
      const dist = Math.abs(y / h - cy);
      const intensity = Math.max(0, 1 - dist * 20);
      const v = Math.floor(intensity * 92);
      buf[idx] = v;       // R
      buf[idx+1] = v + Math.floor(intensity * 163); // G
      buf[idx+2] = v;    // B
    }
  }
  return buf;
}

const w = 320, h = 180, numFrames = 20;
const frames = [];
for (let i = 0; i < numFrames; i++) {
  frames.push({ pixels: makeFrame(i * 0.35, w, h) });
}

writeGIF('/workspace/NOISE.SYS/assets/oscilloscope.gif', w, h, frames, 6);
console.log('GIF written!');
