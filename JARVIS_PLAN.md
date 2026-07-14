# Project "Jarvis" — Build Plan for a Personal Voice AI Assistant

*The product: an Iron-Man-style personal assistant. On screen it's just a
glowing circle. You talk to it, it talks back, and it actually DOES things:
tells you what emails and WhatsApp messages arrived, summarizes them, replies
when you approve, checks your calendar, and knows its owner personally.
Fully personalized per person. The phone-calling agent is a later add-on,
not the core product.*

---

## 1. Why this is possible now (it wasn't in 2015)

Every piece the movie version needed now exists as a rentable API:

| Jarvis ability | Real technology today |
|---|---|
| Understands natural speech | Speech-to-text (Whisper, Deepgram) or realtime speech-to-speech APIs |
| Thinks, decides, plans | LLMs with **tool calling** (Claude API etc.) — the model outputs "call send_email(...)" and our code executes it |
| Speaks with a natural voice | TTS: ElevenLabs, OpenAI voices — near-human quality, low latency |
| Reads/sends your email | Gmail API via Google OAuth (user grants access once, no password stored) |
| Knows your schedule | Google Calendar API |
| WhatsApp messages | WhatsApp Business Cloud API (official) or a WhatsApp-Web bridge (see caveats §4) |
| Remembers you | A memory store per user: profile + running notes + past conversations |
| Wakes on "Hey Jarvis" | Open-source wake-word engines (openWakeWord, Porcupine) |

## 2. The architecture

```
┌──────────────────────────────────────────────────────┐
│  ORB APP (desktop or web) — the glowing circle       │
│  mic in / speaker out, animates while speaking       │
└──────────────┬───────────────────────────────────────┘
               │ audio stream
┌──────────────▼───────────────────────────────────────┐
│  VOICE LOOP                                          │
│  wake word → STT → LLM → TTS                         │
│  (or one realtime speech-to-speech API call)         │
└──────────────┬───────────────────────────────────────┘
               │ tool calls (JSON)
┌──────────────▼───────────────────────────────────────┐
│  ACTION LAYER (our code / MCP servers)               │
│   gmail.list / read / summarize / draft / send       │
│   calendar.today / book / move                       │
│   whatsapp.unread / read / reply                     │
│   web.search, reminders, files...                    │
│   (each new "power" = one new tool — infinitely      │
│    extensible, same pattern as our gesture events)   │
└──────────────┬───────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────┐
│  PERSONALIZATION (per user)                          │
│   profile: name, how to address them, tone, language │
│   standing rules: "never send without asking me"     │
│   memory: facts learned, preferences, history        │
│   connected accounts: their OAuth tokens             │
└──────────────────────────────────────────────────────┘
        + PROACTIVE ENGINE: scheduled checks
          ("8am: summarize inbox and speak the briefing",
           "new important email → announce it")
```

The "circle" is honestly the easy part — a web page with an animated canvas
orb that pulses with the audio. The value is the action layer + memory.

## 3. What a session feels like (the demo script)

> **You:** "Jarvis, what did I miss?"
> **Jarvis:** "Good morning. Since last night you received 9 emails — two need
> you: the lab confirmed Mrs. Khan's crown for Thursday, and your supplier
> raised an invoice question. On WhatsApp, Dr. Ali asked to move Friday's
> meeting. Your first appointment today is at 10."
> **You:** "Reply to Dr. Ali that 2pm works, and draft an answer to the
> supplier saying we paid on the 3rd."
> **Jarvis:** "WhatsApp sent. Here's the supplier draft — want me to read it
> before sending?"

That 60-second interaction IS the sales pitch.

## 4. Honest technical caveats

- **WhatsApp is the tricky one.** The official Cloud API is built for
  *business numbers* messaging customers (works great for the clinic use
  case). Automating a *personal* WhatsApp account is against WhatsApp's terms;
  bridges that link via WhatsApp Web exist and are widely used, but carry a
  small ban risk — be upfront with clients. Safest path: business number via
  the official API + read-and-draft on the desktop app for personal accounts.
- **Latency matters.** For it to feel like Jarvis, replies must start within
  ~1 second — use streaming/realtime APIs, don't wait for full responses.
- **Trust controls are the feature.** Default rule: Jarvis drafts, human
  approves sends. Autonomy can be raised per contact ("auto-confirm
  appointment reschedules") once trust is earned. This is also your safety
  story when selling it.
- **Privacy:** each client's tokens and memory stay isolated per client;
  For dental owners, keep patient-record features out of v1 (HIPAA) — inbox,
  calendar, and business messaging are safe ground.

## 5. Build roadmap

**Phase 1 — the talking core (MVP, sellable demo):**
orb UI + push-to-talk voice loop + Gmail (read/summarize/draft/send with
approval) + Calendar (today/book/move) + per-user profile file. 

**Phase 2 — the Jarvis feel:**
wake word ("Hey Jarvis"), morning voice briefing, WhatsApp integration,
long-term memory ("remember that I prefer morning meetings"), standing rules.

**Phase 3 — enhancements to upsell:**
outbound/inbound phone calling agent (the receptionist we researched — now
it's an add-on, exactly as planned), gesture layer from this repo (point at
an email card on a screen and say "reply to this one"), multi-user per office.

## 6. Business model

- Setup + personalization fee (you configure their accounts, voice, rules)
- Monthly subscription per user — the dental AI market already proved
  business owners pay $200–500/month for assistants that save them time
- Your dental clients = pilot users for Phase 1; their feedback defines
  Phase 2; their testimonial sells it to the next clinic.
