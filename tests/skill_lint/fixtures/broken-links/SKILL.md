---
name: broken-links
---

# Links

Resolves: [ok](references/ok.md), [section](references/ok.md#top), [here](#links).
External is not fetched: [site](https://example.invalid/page), [mail](mailto:a@example.invalid).
Missing: [gone](references/gone.md).
Outside the root: [escape](../bad-skill/SKILL.md).
Absolute: [abs](/etc/hosts).
Bundled file: `references/ok.md` exists, `references/missing.md` does not.

```
[in a fence](references/ignored.md) and `references/ignored.md`
```
