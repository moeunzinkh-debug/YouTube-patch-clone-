# SEA-LION translation provider

SEA-LION is an additional provider for **Voice-over translation**, not a TTS
engine or a replacement for Google, MyMemory or OpenRouter.

1. Patch YouTube with this updated bundle.
2. Open **Morphe settings → Video → Voice-over translation**.
3. Set **Translation provider** to **SEA-LION**.
4. Enter your own **SEA-LION API key** in the masked field.
5. Select your caption language and enable voice-over translation as usual.

Once configured, SEA-LION can also be selected in the player translation sheet.
The player picker asks you to configure the key first if it is missing.

- API base: `https://api.sea-lion.ai/v1/`
- Request endpoint: `POST https://api.sea-lion.ai/v1/chat/completions`
- Model: `aisingapore/Gemma-SEA-LION-v4-27B-IT`
- Authentication: `Authorization: Bearer <your key>`
- Uses OpenAI-compatible streaming responses and numbered caption batches,
  preserving existing segment timings, progressive TTS and seek cancellation.
- Uses a single user message to avoid requiring Gemma system-role support.
- OpenRouter routing/pricing options are not sent to SEA-LION.
- No key is embedded in source or the bundle. The key is stored using the app's
  existing settings mechanism (not a newly encrypted credential store).
- Caption text is sent to SEA-LION only when that provider is selected. Use is
  subject to the provider's account permissions, quotas, pricing and model access.
- API keys may be included in settings exports, just like the existing
  OpenRouter key. The export warning now covers both providers. Do not share
  exported settings containing credentials.

Offline configuration/wiring checks:
`python3 -m unittest discover -s tools/tests -v`.
CI compiles the Android extension and patch bundle. A real authorized API call,
model access, response compatibility, Khmer quality and playback latency still
require testing with a user's account; offline checks do not verify the service.

This update remains on the existing development branch/PR with the EQ shortcut.
No release is published automatically.
