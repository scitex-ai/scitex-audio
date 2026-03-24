## Common Workflows

### "Speak text aloud"

```python
speak("Analysis complete", speed=1.5)
speak("High quality", backend="elevenlabs", speed=1.2)
speak("Offline mode", backend="luxtts", num_threads=8)
```

### "Save audio file"

```python
speak("Recording", output_path="/tmp/alert.mp3", play=False, save=True)
```
