# Security Policy

## Supported versions

| Version            | Supported        |
| ------------------ | ---------------- |
| Latest stable      | ✅               |
| Latest pre-release | ✅ (best-effort) |
| Older releases     | ❌               |

Update to the latest release before reporting. Bugs in old versions are not fixed.

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Use one of these channels:

- **GitHub private reporting:** [Security tab → Report a vulnerability](https://github.com/Jesewe/VioletWing/security/advisories/new)
- **Email:** [jesewescience@outlook.com](mailto:jesewescience@outlook.com)

Include in your report:

- Description of the vulnerability and affected component
- Steps to reproduce
- Potential impact and severity
- Suggested fix, if you have one

You will receive acknowledgment within 5 business days. Keep the issue private until a fix is released.

## Security notes

**Downloads:** Only download VioletWing from the [official GitHub releases page](https://github.com/Jesewe/VioletWing/releases). Third-party distributions may include malware.

**Antivirus flags:** The binary will trigger AV alerts. VioletWing reads another process's memory, which is indistinguishable from malware to most AV engines. Build from source and review the code if you need to verify what it does.

**Data collection:** VioletWing does not collect or transmit personal data. Forks and modifications must maintain this.

**Online play:** Using VioletWing in online matchmaking violates CS2's Terms of Service. This is a user responsibility, not a security issue.
