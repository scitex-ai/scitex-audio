## Available Backends

| Backend | Quality | Offline | Default Speed | Notes |
|---------|---------|---------|---------------|-------|
| `elevenlabs` | Highest | No | x1.2 | Paid API key required |
| `luxtts` | High | Yes | x2.0 | Open-source, voice cloning, 48kHz |
| `gtts` | Medium | No | x1.5 | Free, Google TTS |
| `pyttsx3` | Basic | Yes | native | System TTS (espeak) |

Fallback order: elevenlabs -> luxtts -> gtts -> pyttsx3
