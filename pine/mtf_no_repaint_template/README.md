MTF No-Repaint Template (Pine v6)

## What is this?

A minimal Pine Script v6 template for building multi-timeframe (MTF) indicators without repainting. It shows how to safely request higher-timeframe data, align it to the chart timeframe, and generate signals only on confirmed bar closes.

## How to use

- Start from `mtf_no_repaint_template_v6.pine`.
- Replace the placeholder logic with your indicator calculations.
- If you request HTF data, use `request.security()` with `barmerge.gaps_off` and reference `[1]` where necessary to avoid forward-looking artifacts.
- Emit signals/alerts only on bar close. Avoid using `real-time` values of HTF sources within the same bar.

## No-repaint guidelines

- Use one-bar shift (`[1]`) on levels derived from the current bar when needed.
- For MTF inputs, avoid `lookahead_on`; prefer `lookahead=barmerge.lookahead_off`.
- Avoid storing history-dependent function calls inside short-circuiting conditionals; compute first, then use the variables.
- Do not specify `timeframe` in `indicator()` when using labels/alerts (side effects).

## Disclaimer

Educational purposes only. Not financial advice. Trading involves risk.
