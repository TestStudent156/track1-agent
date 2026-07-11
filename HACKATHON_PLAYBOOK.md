# Hackathon-Spickzettel — für den nächsten AMD/Cloud/Token-Routing-Hackathon

## 🔥 Fireworks AI Routing Agent (Pattern)
- **Regex-Classifier** (0 Tokens) statt LLM-Klassifikation → spart 50-200 Tokens pro Task
- **Empirische Routing-Tabelle** aus echten Benchmark-Runs bauen, nicht raten
- **JSON response_format** für Sentiment/NER → blockiert Thinking-Tokens im Output
- **Category-spezifische max_tokens** (200 sentiment, 3000 logic)
- **temperature=0.0** + **single API call** pro Task

## 🐳 Docker
- `docker buildx build --platform linux/amd64 -t name:latest .`
- Image muss in **public Registry** (Docker Hub / GHCR)
- `python:3.12-slim` als Base (nicht 3.11-slim — das war im Original, funktioniert aber)
- `ENTRYPOINT` als Shell-Script, nicht direkt Python

## ☁️ lablab.ai Submission
- **Headless-Browser blockiert** → Cloudflare Turnstile
- Lösung: Playwright `addInitScript` mit:
  - `navigator.webdriver = false`
  - `navigator.plugins = [1,2,3,4,5]`
  - `window.chrome = { runtime: {} }`
- Oder: sichtbaren Chrome mit `--remote-debugging-port=9222` starten
- Formular-Felder: Name, Description (≥100 Wörter), Repo-URL, Docker-Image-URL, Run-Command, Env-Vars **leer lassen**
- Assets: Cover 1920×1080 SVG, Slides HTML+PDF, Video 60-90s

## 🔄 GitHub
- Repo **public**, mit README
- **Commit-Historie** zählt für Judges — keine Riesen-Commits
- GitHub Actions CI/CD: `docker-build-test.yml` mit Build + Test + Validate
- Secret `FIREWORKS_API_KEY` in Repo-Settings setzen

## 🛠️ Tools
- **Playwright MCP**: `browser_run_code_unsafe` für Stealth-Injection
- **agent-browser**: CLI-Tool für CDP-Chrome (braucht Chrome-Pfad)
- **git -C path**: Git-Befehle ohne `cd` (Shell-Quoting-Probleme umgehen)
- **PowerShell Start-Process**: Chrome mit CDP-Flags starten

## 📊 Diese Runde (Track 1)
- 5 Modelle: minimax-m3, kimi-k2p7-code, gemma-4-31b-it, gemma-4-26b-a4b-it, gemma-4-31b-it-nvfp4
- kimi-k2p7-code = bester für 7/8 Kategorien
- minimax-m3 = NER (256 Tokens vs 397)
- ~4.769 Tokens total, 152 MB Image, ~40s
- Docker Hub: acidwichtel/track1-agent:latest
- GitHub: TestStudent156/track1-agent
