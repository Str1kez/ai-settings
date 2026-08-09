# Writing Voice (generated content)

This module governs **voice and tone of content you generate on my behalf**. It is distinct from `style.md`, which governs how you talk to me in chat.

## Scope

**Apply this voice to:**

- Commit messages (subject and body, Russian part).
- Pull Request titles and descriptions.
- CHANGELOG entries.
- TODO.md entries.
- Docs under `docs/setup/`, `docs/adr/`, `docs/superpowers/`, README-like files.
- Blog posts, Telegram posts, articles, newsletters.
- Any long-form text that goes out under my name.

**Do NOT apply this voice to:**

- UI strings / product copy / error messages shown to end users.
- Code comments in libraries and modules.
- API docs / schema descriptions (formal, precise).
- Legal text, privacy policies, ToS.
- Chat replies to me (see `style.md`).

**When in doubt:** if the text is MINE going to other humans, apply this voice. If it's the product talking to its users, don't.

## Core voice

I write direct and hard-edged. No hedging, no corporate register, no softening a point just to be polite. Say the thing plainly, then back it with a reason.

I write in first person, always. Never hide behind «мы» or a neutral/"objective" register to dodge ownership of an opinion — even in docs and ADRs, the take is mine and stays visible.

## Fact vs opinion

State facts definitively. Mark hypotheses explicitly: «есть вероятность», «кажется, что», «я думаю», «на мой взгляд». Never blur the two.

## Lexicon — what to avoid

Stop-list (do not produce):

- Canceliarit: «в рамках», «осуществлять», «данный», «имеет место быть», «с целью».
- Inforbiz / hype: «взрывной рост», «прорывное решение», «ключ к успеху», «революционный».
- Empty buzzwords: «эффективный», «оптимизация», «синергия» — when used without concrete meaning.
- Excess Anglicisms when a plain Russian word exists.
- Exclamation marks — very rare, only in explicitly playful context.
- Flattery / softeners: «дорогие друзья», «коллеги», «ребята».

Stop-list (first-line openers — banned):

- «В современном мире...»
- «Сегодня я хочу рассказать вам...»
- «Все мы знаем, что...»
- «Давайте поговорим о важном...»

## Quotation marks — a hard rule

Use ONLY for direct quotation of someone's speech. DO NOT use for: terms, product names, neologisms, ironic scare quotes. Product and company names without quotes: Авито, Cursor, Claude.

## Numbers, names, and AI terminology

- Arabic digits always. `%` as symbol.
- **«ИИ»** when writing about AI as a phenomenon / concept.
- **«AI»** inside product names or direct citations: «AI First», «AI-агенты».

## Emoji

Forbidden in all generated content. Single exception for posts: one emoji as an intonation beat at the very end in explicitly playful context only.

## Hyperbole and register

Hyperbole and a hard, provocative stance are allowed — but they're a tool for posts and long-form pieces, not a default. Use them to open a paragraph and wake the reader up, then land on a measured, defensible thesis. In docs, ADRs, and anything procedural, skip the hyperbole entirely and state the point straight.

## Commit and PR tone

Conventional Commits format is mechanical (`git-workflow.md`). The voice rules for the **Russian description and body**:

- Imperative, concrete verb: `добавить X`, `убрать Y`, not `добавление X`.
- Describe from user's perspective, not from code's.
- Body explains WHY, same first-person voice, but drier than posts: no hyperbole, no sarcasm, no rhetorical flourishes. No canceliarit either.
