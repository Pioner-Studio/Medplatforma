# PATCH_FORMAT

## Вариант A — Drop‑in replacement

Присылаю целый файл, который ты просто заменяешь 1:1.

## Вариант B — Патч‑вставка по якорям

Формат:

=== PATCH: templates/calendar.html ===
AFTER: <!-- quick-move buttons -->
INSERT:

<div class="btns">
<button id="plus15">+15</button>
<button id="plus30">+30</button>
</div>
=== END PATCH ===

Альтернатива по линиям:

=== PATCH: main.py ===
RANGE: L210-L248 (заменить целиком)
REPLACE_WITH:

# новый код здесь…

=== END PATCH ===

Правила:

- Каждый патч содержит ровно один файл.
- Якорь (AFTER/BEFORE) должен существовать в файле.
- Если якоря нет → сначала присылай актуальный файл.
