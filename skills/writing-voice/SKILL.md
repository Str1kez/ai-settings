---
name: writing-voice
version: 1.0.0
description: |
  Use when writing text that goes out to people under the user's name: PR title and
  description, CHANGELOG or TODO entry, docs, README, ADR, spec, post, article.
  SKIP: commit messages (English, see `en-commit-message`), UI strings, error messages for end users, code comments, API docs and
  schema descriptions, legal text, chat replies to the user (see `style.md`).
category: code
tags: [writing, voice, russian]
---

# Writing Voice (generated content)

Voice and tone of content generated on the user's behalf. Distinct from `style.md`, which governs chat. If the text is the user's going to other humans, apply this voice. If it is the product talking to its users, don't.

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

## PR tone

The PR title and description are in Russian. Format and template live in skill `ru-pr-description`. The voice rules:

- Imperative, concrete verb in the title: `добавить X`, `убрать Y`, not `добавление X`.
- Describe from the user's perspective, not from the code's.
- The body explains WHY, same first-person voice, but drier than posts: no hyperbole, no sarcasm, no rhetorical flourishes. No canceliarit either.
