# JARVIS Skill ve Plugin Envanteri

Son guncelleme: 2026-10-28

## Ozet

- Skill: 17
- Claude plugin: 51
- Official plugin: 36
- External plugin: 15
- MCP bilesenli plugin: 16
- Kodlama / code review / LSP / MCP odakli plugin: 45

## Skill Listesi

1. `algorithmic-art`: Kodla uretken gorsel sanat, p5.js, seed'li randomness, flow field ve particle sistemleri.
2. `brand-guidelines`: Anthropic marka renkleri, tipografi ve gorsel standartlarini artifact'lere uygular.
3. `canvas-design`: Poster, statik gorsel, PNG/PDF tasarim ve kompozisyon uretimi.
4. `claude-api`: Claude API, Anthropic SDK, model parametreleri, streaming, tool use, MCP ve migration referansi.
5. `doc-coauthoring`: Dokuman, proposal, teknik spec, karar dokumani ve struktur yazim workflow'u.
6. `docx`: Word `.docx` okuma, yazma, duzenleme, bicimlendirme, tablo/heading/gorsel islemleri.
7. `frontend-design`: UI/UX estetik yon, tipografi, layout ve tasarim kalitesi rehberi.
8. `internal-comms`: Status report, leadership update, FAQ, incident report ve sirket ici iletisim formatlari.
9. `mcp-builder`: Python/Node MCP server tasarimi, tool design, auth ve deployment rehberi.
10. `pdf`: PDF okuma, ozetleme, tablo/metin cikarma, birlestirme, bolme, watermark, form, sifreleme ve OCR.
11. `pptx`: PowerPoint sunu okuma, olusturma, duzenleme, pitch deck ve slide icerigi islemleri.
12. `skill-creator`: Yeni skill yaratma, mevcut skill'i iyilestirme, eval ve performans olcumu.
13. `slack-gif-creator`: Slack uyumlu animasyonlu GIF uretimi ve validasyonlari.
14. `theme-factory`: Dokuman, slide, HTML ve artifact'lere hazir veya ozel tema uygulama.
15. `web-artifacts-builder`: React/Tailwind/shadcn tabanli karmasik HTML artifact ve web app uretimi.
16. `webapp-testing`: Playwright ile lokal web app test, screenshot, browser log ve UI dogrulama.
17. `xlsx`: Excel/CSV/TSV okuma, duzenleme, formul, grafik, veri temizleme ve spreadsheet uretimi.

## Official Claude Pluginleri

1. `agent-sdk-dev`: Claude Agent SDK gelistirme workflow'lari.
2. `clangd-lsp`: C/C++ clangd language server entegrasyonu.
3. `claude-code-setup`: Kod tabanini analiz edip Claude Code hook, skill, MCP ve subagent onerileri uretir.
4. `claude-md-management`: `CLAUDE.md` audit, session learning yakalama ve proje hafizasi yonetimi.
5. `code-modernization`: Legacy kod modernizasyonu, topology, rule extraction, transform ve hardening workflow'u.
6. `code-review`: Pull request/code review icin coklu ajan ve confidence scoring.
7. `code-simplifier`: Kodu sadelestirme, okunabilirlik ve maintainability iyilestirme ajani.
8. `commit-commands`: Git commit, push ve PR olusturma komutlari.
9. `csharp-lsp`: C# language server destegi.
10. `cwc-makers`: Code-with-Claude Makers Cardputer setup/flash/onboarding komutlari.
11. `example-plugin`: Command, agent, skill, hook ve MCP iceren ornek plugin.
12. `explanatory-output-style`: Kod kararlarini egitici sekilde aciklayan output-style hook'u.
13. `feature-dev`: Feature gelistirme icin exploration, architecture ve quality review ajanlari.
14. `frontend-design`: Frontend UI/UX implementation skill'i.
15. `gopls-lsp`: Go language server destegi.
16. `hookify`: Davranis kaliplarindan hook olusturma ve hook yonetimi.
17. `jdtls-lsp`: Java language server destegi.
18. `kotlin-lsp`: Kotlin LSP, code intelligence ve refactor destegi.
19. `learning-output-style`: Interaktif ogrenme modu hook'u.
20. `lua-lsp`: Lua language server destegi.
21. `math-olympiad`: Yarismaci matematik cozumu ve adversarial proof verification.
22. `mcp-server-dev`: MCP server tasarim, deployment, auth ve interactive MCP app rehberi.
23. `mcp-tunnels`: Private MCP server'i Anthropic MCP tunnel ile baglama.
24. `php-lsp`: PHP language server destegi.
25. `playground`: Interaktif tek dosya HTML playground uretimi.
26. `plugin-dev`: Agent, command, hook, MCP ve plugin yapisi gelistirme toolkit'i.
27. `pr-review-toolkit`: PR review icin comments, tests, error handling, type design ve quality ajanlari.
28. `pyright-lsp`: Python Pyright language server destegi.
29. `ralph-loop`: Iteratif Claude loop workflow'u.
30. `ruby-lsp`: Ruby language server destegi.
31. `rust-analyzer-lsp`: Rust analyzer language server destegi.
32. `security-guidance`: Injection, XSS, SSRF, hardcoded secret ve diger guvenlik riskleri icin review hook/ajanlari.
33. `session-report`: Oturum raporu / session summary skill'i.
34. `skill-creator`: Skill yaratma, optimize etme ve benchmark workflow'u.
35. `swift-lsp`: Swift language server destegi.
36. `typescript-lsp`: TypeScript language server destegi.

## External Claude Pluginleri

1. `asana`: Asana task/proje yonetimi MCP entegrasyonu.
2. `context7`: Guncel dokumantasyon ve kod ornekleri getiren Context7 MCP.
3. `discord`: Discord kanal messaging bridge, allowlist ve access policy.
4. `fakechat`: Local iMessage benzeri test chat yuzeyi.
5. `firebase`: Firebase Firestore, Auth, Functions, Hosting ve Storage MCP.
6. `github`: GitHub repo, issue, PR, code review ve search MCP.
7. `gitlab`: GitLab repo, merge request, CI/CD, issue ve wiki MCP.
8. `greptile`: GitHub/GitLab AI code review comment yonetimi.
9. `imessage`: iMessage bridge ve access policy.
10. `laravel-boost`: Laravel Artisan, Eloquent, route, migration ve framework yardimi.
11. `linear`: Linear issue/project/status/search entegrasyonu.
12. `playwright`: Microsoft Playwright MCP ile browser automation ve E2E test.
13. `serena`: Semantic code analysis, refactor ve codebase navigation MCP.
14. `telegram`: Telegram messaging bridge, allowlist ve access policy.
15. `terraform`: Terraform/IaC MCP otomasyon ve interaction destegi.

## Claude Kod Yazma Durumu

Jarvis'e Claude'un kodlama ekosistemi iki seviyede baglandi:

1. Workflow/plugin/skill seviyesi: Code review, feature development, plugin development, MCP builder, LSP ve frontend design gibi Claude Code kaynaklari Jarvis tarafindan okunup uygulanabilir.
2. API seviyesi: `claude_code_assistant` araci eklendi. `config/.env` icine `CLAUDE_API_KEY` girilirse Claude API ile kod yazma, kod inceleme, refactor onerisi ve feature planlama yapabilir.

Ana konusma modeli Gemini Live olarak kalir; Claude API anahtari eklenirse Jarvis belirli kodlama islerinde Claude'u ikinci uzman model olarak cagirabilir.
