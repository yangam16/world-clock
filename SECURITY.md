# Security policy / 安全报告

## Reporting a vulnerability

Use GitHub's [private vulnerability reporting](https://github.com/yangam16/world-clock/security/advisories/new) when available. Include the affected version, a minimal reproduction using synthetic data, and the likely impact. Do not publish credentials, actual note contents, or exploit details in a public Issue.

If private reporting is unavailable, open a minimal Issue requesting a private reporting channel, without sensitive details. No response-time or security-update SLA is promised.

Only the current `main` branch and latest release are actively considered for fixes. Older releases may require an upgrade.

## Data handling

- Drafts are local UTF-8 files and are not encrypted.
- Snapshot exports are independent files selected by the user.
- Source archives use an explicit public-file allowlist. Runtime drafts, settings, caches and local dependency packages are excluded.
- The app does not implement cloud sync or require API keys.
- Remove private content from logs and screenshots before submitting reports.

## 中文

安全问题请优先使用 GitHub [私密漏洞报告](https://github.com/yangam16/world-clock/security/advisories/new)。若入口不可用，请仅提交一个请求私密沟通渠道的 Issue，不附带漏洞细节、真实便签或凭据。请提供版本、合成数据复现步骤和影响范围。

本项目未承诺安全响应时限。主要维护当前 main 和最新版本；便签为未加密的本地文本，请自行保护文件与备份。
