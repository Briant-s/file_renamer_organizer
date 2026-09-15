# Distribution & Commercialization Strategy
### AI File Renamer & Organizer

---

## What We're Distributing

A desktop software tool that runs entirely on the user's machine — no internet connection required for core functionality, no subscription to external AI services, and no user data ever leaves the device.

This is the core differentiator: **local, private, and offline-first.**

---

## How Users Will Receive the Product

### Target Experience
The user downloads a single installer file, runs it like any normal software (e.g. Microsoft Word, VLC), and the tool is ready to use. No technical setup required.

### Delivery Method
- **Windows:** A standard `.exe` installer — identical experience to installing any commercial software
- **macOS / Linux:** Equivalent native installers for each platform
- **Distribution channel:** Direct download from a product website, or listed on platforms like Gumroad, Lemon Squeezy, or the Microsoft Store

### One External Dependency
The tool relies on **Ollama**, a free open-source application that runs AI models locally on the user's machine. This is a one-time installation, similar to how some software requires a runtime like Java or .NET.

Options for handling this:
1. Bundle the Ollama installer inside our own installer — seamless, one-click setup
2. Direct users to install Ollama separately with clear instructions — simpler to maintain

---

## Licensing & Access Control

To sell the product, access is gated behind a **license key** — a unique code the user receives after purchase.

### How It Works
1. Customer purchases through our storefront
2. They receive a unique license key via email (e.g. `XXXX-XXXX-XXXX-XXXX`)
3. On first launch, the tool asks for the key
4. The key is verified against our server — if valid, the tool activates and the key is saved locally
5. Subsequent launches work offline — no repeated internet checks

### Key Generation & Validation
Keys are cryptographically generated, meaning each key is mathematically unique and verifiable. This prevents users from sharing or guessing keys.

### Infrastructure Required
- A lightweight server (estimated cost: **$5–10/month**) to validate license keys
- A storefront (Gumroad or Lemon Squeezy — **0% to 5% transaction fee**, no monthly cost)

---

## Piracy & Code Protection

No software protection is absolute — determined technical users can always find workarounds. The goal is to make piracy inconvenient enough that most users simply pay.

### Measures Taken
| Measure | What It Does | Strength |
|---|---|---|
| License key validation | Requires a valid purchase to activate | Medium |
| Code obfuscation (PyArmor) | Makes source code unreadable if extracted | Medium |
| Online activation | Keys can be deactivated remotely if abused | Medium |

### Honest Limitations
- A sufficiently skilled developer could reverse-engineer the tool
- The underlying AI model (Ollama) and core libraries are open source — the code structure is not a secret
- **The real competitive moat is not the code itself** — it is the user experience, prompt quality, workflow design, and brand trust built over time

---

## Pricing Model Options

| Model | Description | Best For |
|---|---|---|
| **One-time purchase** | Pay once, use forever | Simpler, lower friction, good for early traction |
| **Annual license** | Renew yearly for updates | Predictable recurring revenue |
| **Freemium** | Free tier (limited files/month), paid tier unlocks full use | Maximizes top-of-funnel, converts power users |
| **Per-seat (B2B)** | License per employee for business customers | Higher revenue per deal, longer sales cycle |

**Recommended starting point:** One-time purchase at a low introductory price to build early user base and gather feedback, with a path toward annual licensing as the product matures.

---

## Go-to-Market Path

```
Phase 1 — Validate (Now)
└── Working prototype demo
└── Gather feedback from target users

Phase 2 — Package (1–2 months)
└── Build Windows installer
└── Set up storefront + license key system
└── Basic product website

Phase 3 — Launch (3–4 months)
└── Soft launch to early adopters
└── Collect reviews and testimonials
└── Iterate on UX and model quality

Phase 4 — Expand (6+ months)
└── macOS and Linux installers
└── B2B / team licensing
└── Potential Microsoft Store listing
```

---

## Summary of Costs to Launch

| Item | Estimated Cost |
|---|---|
| License key server (VPS) | ~$5–10/month |
| Storefront (Gumroad/Lemon Squeezy) | 0–5% per transaction |
| Domain + basic website | ~$15/year |
| Developer tools (PyInstaller, Inno Setup) | Free |
| **Total fixed monthly cost** | **~$10–15/month** |

The marginal cost per additional user is effectively zero — no cloud AI costs, no per-user infrastructure.
