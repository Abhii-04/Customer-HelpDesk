# Suggestions and improvements

These are recommendations only; no additional functions were implemented.

- Connect the human route and rejected replies to your actual support queue before using this with customers. There is currently no ticket creation or handoff integration.
- Confirm the DeepSeek model names available to your account and set `SMALL_LLM`/`BIG_LLM` accordingly. Both retain your original model default.
- Replace the sample order records with your actual backend. Malformed dates were corrected to valid demo dates; delivered orders use 2026-10-08. Confirm the brass diya price: the order has Rs 499 while the catalog has Rs 899.
- Calibrate Laya classification and checker thresholds against representative customer messages. Existing threshold comments are not evidence of calibration for Laya.
- Decide what the complexity signal should do. It is collected as a choice, but the existing decision function routes by intent, confidence and human requests.
- If multi-turn support is needed, preserve conversation context; the current CLI processes one message per run.
- Consider explicit customer-facing handling for model download, provider authentication, and inference failures. Errors currently surface to the caller.
- The cached Laya checkpoint emitted a temperature-clamping warning during live verification. Review its calibration before relying on confidence thresholds in production.

## Verification

- Dependency sync and Python compilation passed.
- All five CLI routes, route precedence, order tools, reply-check boundaries and withheld replies passed with inference mocked. DeepSeek message forwarding was checked with a mocked provider.
- A real offline run using the cached Laya model successfully classified, looked up and checked `KH-1042`, returning its shipping status.
- Live DeepSeek calls were not tested because no `DEEPSEEK_API_KEY` is configured.
