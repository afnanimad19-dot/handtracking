# Competitor Research — Who's Making Money & Which Niche To Pick

*Research date: July 2026. Follow-up to [RESEARCH.md](RESEARCH.md). Questions:
who is already selling this to business owners, in which niches, which niche
should we enter (healthcare/dental is our warm market), and what would it take
to build the "Jarvis" voice assistant on top.*

---

## 1. Companies already selling GESTURE control to businesses

| Company | Niche | Notes |
|---|---|---|
| [Ultraleap](https://docs.ultraleap.com/hand-tracking/index.html) | Hand-tracking hardware + SDK (kiosks, XR, automotive) | The biggest name (ex-Leap Motion). Sells camera modules + "TouchFree" kiosk software to enterprises. |
| [GestureTek](http://productsummary.gesturetek.com/) | Interactive advertising, digital signage, museums, presentation systems | One of the oldest players — sells installed systems to brands, malls, airports. |
| [ManoMotion](https://www.manomotion.com/gesture-control/) | Camera-only gesture SDK (like our approach) for cars, kiosks, smart rooms, industrial safety | Closest to what we do: pure software on normal cameras, licensed to brands and developers. |

**In medical specifically** (sterile, touch-free control of screens):

- [TedCas](https://tedcas.com/en/home-2/) (Spain, since 2011) — gesture + voice control of
  medical equipment so doctors avoid contact infections in the OR.
- [GestSure](https://www.crunchbase.com/organization/gestsure) (Toronto, since 2011) —
  touchless control of imaging (PACS) for surgeons and radiologists.
- Gesture-controlled image navigation has been validated **in dental surgery
  specifically** — published case series exist:
  [touchless image navigation in dental surgery (PMC)](https://ncbi.nlm.nih.gov/pmc/articles/PMC4061300),
  [operating-room gesture research](https://arxiv.org/pdf/1611.04138).

**Takeaway:** the gesture-only market is real but niche — small companies selling
installations and SDKs. It's a good *differentiator and demo*, not the main
money-maker by itself.

## 2. Where the money ACTUALLY is in dental right now: AI voice receptionists

This market is proven and growing fast — and it matches your "AI you can talk
to, connected to the back end" vision almost exactly:

- [Arini](https://www.arini.ai/) — "AI receptionist for dentists," Y Combinator
  W24, deployed across hundreds of dental offices. Answers calls 24/7, books
  appointments directly into dental practice software (Dentrix, Eaglesoft,
  Open Dental). Pricing: mid three figures per month **per location**.
  Reported results: 90%+ call answer rate, and practices recovering
  **$100k–150k/year in missed production** ([case data](https://www.arini.ai/blog/ai-receptionist-dental-practices-arizona)).
- Other players: Weave, Dental Intelligence, RevenueWell, Goodcall,
  My AI Front Desk, AINORA, Orthia — market comparison:
  [7 best AI receptionists for dental (2026)](https://ainora.lt/blog/ai-voice-agent-dental-clinics-2026),
  [dental AI receptionist competition](https://orthia.io/blog/dental-ai-receptionist-competition).
- Typical pricing across the market: **$200–$500/month per clinic** (budget tools
  from $49, premium $800+), or $0.05–$0.20 per call-minute.

**Takeaway:** dental clinics are *already paying monthly subscriptions* for AI
assistants. This is the proven revenue model to copy — and you already have
dental clients to pilot with.

## 3. The "Jarvis" idea — who's doing personalized voice AI assistants

The circle-on-screen, talk-to-it, connected-to-your-Gmail assistant exists but
no one owns the market yet:

- [alfred_](https://get-alfred.ai/blog/best-ai-personal-assistants) — proactive
  Gmail/Outlook triage, drafts in your voice, morning briefings.
- [Jarvis (tryjarvis.app)](https://tryjarvis.app/) — ultra-realistic voice
  (ElevenLabs), connects Gmail, iMessage, WhatsApp; sub-second responses.
- [Lindy AI](https://get-alfred.ai/blog/best-ai-personal-assistants) —
  $50–100/month, 100+ integrations, build-your-own agent workflows.
- Google Gemini — deep Workspace integration but reactive, not proactive.
- Open-source: [isair/jarvis](https://github.com/isair/jarvis) — private,
  offline voice assistant with unlimited tool/MCP support (good architecture
  reference).

**Takeaway:** general "Jarvis for everyone" is crowded with well-funded players.
"Jarvis for a specific business type, personalized per owner, installed and
supported by us" is where a small team wins — big players don't do hands-on
setup for a single dental office; you can.

## 4. Recommendation: the dental/healthcare niche is the right call

You have dental/healthcare clients = free pilot sites, references, and real
feedback. That beats any market analysis. The winning package for one clinic:

1. **AI front-desk voice assistant** (the circle + voice): answers/handles
   patient questions, checks the calendar, books appointments, sends reminders.
   Personalized per clinic — its own name, voice, knowledge of the clinic's
   services and prices. *This is the part clinics provably pay $200–500/mo for.*
2. **Owner's "Jarvis" back-office briefing**: connected to the clinic's
   Gmail/Calendar — "You got 14 emails today, 3 need replies, here are drafts;
   two patients asked to reschedule; want me to confirm?" Reply by voice.
3. **Gesture layer as the differentiator**: our pinch/drag tech for
   (a) touch-free control of X-ray/scan images in the treatment room (sterile,
   gloves on — validated use case in dental surgery), and
   (b) a waiting-room interactive screen (services, before/after galleries).
   No competitor bundles this — it makes the demo unforgettable.

**Pilot plan:** build for ONE existing client, free or cheap, for 1–2 months.
Measure missed calls recovered and hours saved. Turn that into a case study,
then price at ~$300–500/month per clinic like the market does.

## 5. How the Jarvis would be built (high-level architecture)

```
 Mic/Speaker ("the circle" UI - web or desktop app)
      │  realtime speech <-> speech
      ▼
 Realtime voice AI (e.g. Claude API / realtime voice APIs + ElevenLabs TTS)
      │  function calls ("tools")
      ▼
 Tool layer (MCP servers or custom):
   - Gmail: list/read/summarize/draft/send
   - Google Calendar: check/book/reschedule
   - SMS/WhatsApp: read + reply
   - Clinic data: services, prices, FAQs (per-client knowledge base)
      │
      ▼
 Personalization profile per client:
   - name/voice/personality, business facts, standing rules
     ("always confirm before sending anything")
 Memory: conversation + preference history per user
```

Key build notes:
- The LLM does the thinking; **tools** do the doing (read Gmail, send reply,
  book slot). This is the same "function calling" pattern as our gesture events
  — an event/command comes in, code executes the action.
- Gmail/Calendar access is via Google OAuth per client (they log in once and
  grant access — you never store their password).
- **Healthcare caveat:** patient data means HIPAA (US) / privacy rules.
  Start the pilot with non-patient data (owner's business inbox, bookings,
  general questions) and add patient-data features with proper compliance later.
- The gesture engine (`gestures.py`) plugs in as just another input: pinch/point
  events can drive the same tool layer the voice does — point at an email card
  and say "reply to this one."
