ElevenLabs Flash v2.5 — Quickstart

What is it
- eleven_flash_v2_5 is the ultra‑low latency TTS model (~75ms excluding network/app). Best for real‑time agents and interactive apps.
- Supports 32+ languages. If you need stronger number/date normalization, consider multilingual_v2 or enable text normalization (Enterprise only).

Prerequisites
- Get an API key from ElevenLabs and set: XI_API_KEY=your_key
- Pick a voice_id (e.g., “aria”). Voices live under your account.

A) One-shot HTTP TTS (fastest way to test)
- Use when you just want audio from a text string.
- You’ll get an audio file (mp3/wav/etc) in the response body.

Example: curl
curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/aria" \
  -H "xi-api-key: $XI_API_KEY" \
  -H "Content-Type: application/json" \
  --data '{
    "model_id": "eleven_flash_v2_5",
    "text": "Hello there! This is Flash v2.5 in action.",
    "output_format": "mp3_22050_32"
  }' --output output.mp3

Example: Node.js (HTTP)
import fs from "node:fs";
import fetch from "node-fetch";

const XI_API_KEY = process.env.XI_API_KEY;
const VOICE_ID = "aria";

async function ttsOnce(text) {
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`, {
    method: "POST",
    headers: {
      "xi-api-key": XI_API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model_id: "eleven_flash_v2_5",
      text,
      output_format: "mp3_22050_32"
    })
  });

  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const audio = await res.arrayBuffer();
  fs.writeFileSync("output.mp3", Buffer.from(audio));
  console.log("Saved output.mp3");
}

ttsOnce("Hello! Ultra-low latency TTS, nice to meet you.");

B) Realtime WebSocket streaming (for agents)
- Use when you need partial audio quickly and you’ll send multiple short messages.
- Only generation time counts toward concurrency; the open socket itself is cheap.

Protocol basics
- Connect: wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?auto_mode=true&output_format=mp3_22050_32
- Header: xi-api-key: YOUR_API_KEY
- Send JSON messages: {"text": "..."}; flush with {"text": ""} to get audio now.
- Receive server messages with fields like { audio, isFinal }. audio is base64 chunks.

Example: Node.js (WebSocket)
import WebSocket from "ws";

const XI_API_KEY = process.env.XI_API_KEY;
const VOICE_ID = "aria";
const OUTPUT_FORMAT = "mp3_22050_32";

const url = `wss://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}/stream-input?auto_mode=true&output_format=${OUTPUT_FORMAT}`;
const ws = new WebSocket(url, { headers: { "xi-api-key": XI_API_KEY } });

ws.on("open", () => {
  // Init (empty text starts the session)
  ws.send(JSON.stringify({ text: "" }));

  // Send a short line to speak
  ws.send(JSON.stringify({ text: "Hi! This is a realtime demo." }));

  // Flush so the server starts streaming audio now
  ws.send(JSON.stringify({ text: "" }));
});

ws.on("message", (msg) => {
  const data = JSON.parse(msg.toString());

  if (data.audio) {
    // data.audio is base64 audio; append to a buffer or stream to player
    // For demo, we’ll just log chunk sizes
    console.log("Audio chunk bytes:", Buffer.from(data.audio, "base64").length);
  }

  if (data.isFinal) {
    console.log("Stream finished.");
    ws.close();
  }
});

ws.on("error", (err) => console.error("WebSocket error:", err));
ws.on("close", () => console.log("WebSocket closed."));

C) Practical tips
- Character limits: Flash v2.5 supports ~40,000 chars per request (~40 minutes audio). For longer text, chunk it.
- Latency: ~75ms for first audio byte, excluding your network/app overhead.
- Numbers/dates: Flash v2.5 keeps normalization off by default to preserve speed. If your speech includes phone numbers, dates, or currencies, normalize text on your side (LLM pre-processing) or use apply_text_normalization="on" (Enterprise) or switch to multilingual_v2 for better normalization.
- Languages: Flash v2.5 covers all multilingual_v2 languages plus Hungarian, Norwegian, Vietnamese.
- Concurrency: On WebSocket, only generation time counts. Scale by simulating realistic dialogue patterns (short bursts of ~150 chars, ~10s pauses).

D) Minimal request bodies you’ll reuse
HTTP body (MP3)
{
  "model_id": "eleven_flash_v2_5",
  "text": "Your text here",
  "output_format": "mp3_22050_32"
}

WebSocket messages
// Start session
{ "text": "" }
// Speak
{ "text": "Your short phrase here." }
// Flush/start streaming now
{ "text": "" }

E) Troubleshooting
- No audio in first message: ensure you sent a non-empty text, then a flush {"text": ""}.
- Wrong header casing: xi-api-key must match exactly.
- Big inputs stall agents: split text into small phrases (50–200 chars), stream per turn.
- Need higher quality than Flash: switch to turbo_v2_5 or multilingual_v2 (trade latency for quality).