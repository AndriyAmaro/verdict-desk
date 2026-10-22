# VERDICT DESK — demo script v4 (record-ready)

**Target: 100 seconds.** Why v4: the previous script showed the dashboard and the command line, but
not the three things that now lead the field — the lab, the exhibit of an anchored record, and the
replay. A judge who watches 100 seconds should see a claim, then see it verified.

Before recording: run `gh workflow run hourly.yml` and wait for `pages` to go green, so the numbers
on screen are the live ones. Never record against a stale copy: if the ledger grows, the number in
the video and the page a judge opens will disagree, which is the one thing this project cannot
afford.

---

## Shot list

| # | Time | Screen | Action | Caption (burn in) |
|---|---|---|---|---|
| 1 | 0:00–0:09 | `andriyamaro.github.io/verdict-desk/` | Dashboard loaded, green banner | **113 decisions. Every hash recomputed in this browser.** |
| 2 | 0:09–0:22 | Same, tamper panel | Press **"Test the chain"** → row turns red, banner says the chain no longer verifies | **Edit one character and the trail breaks — in your browser, not on my server.** |
| 3 | 0:22–0:26 | Same | Press **"Restore the real ledger"** | *(no caption; let it settle)* |
| 4 | 0:26–0:42 | `verdict-desk/lab.html` | Pick a dossier, scroll to section 3, point at the single red row | **Which argument decided it? Remove one and the verdict changes.** |
| 5 | 0:42–0:52 | Same, playground | Drag bull weight up, then ATR up | **Move the inputs. The rule that fires is named, not hidden.** |
| 6 | 0:52–1:08 | `verdict-desk/exhibit/exhibit-80.html` | Scroll sections 1 → 2 → 3 | **One decision as a document: evidence, each claim beside the text it cites, the deciding argument.** |
| 7 | 1:08–1:14 | Same, section 6 | Hold on the integrity table | **And the record still matches the hash written on Ethereum Sepolia.** |
| 8 | 1:14–1:22 | Terminal | `python3 -m verdict_desk replay` | **113 verdicts re-derived from their frozen evidence. 113 matches.** |
| 9 | 1:22–1:28 | Terminal | `python3 -m verdict_desk monitor` | **The published ledger still matches the chain.** |
| 10 | 1:28–1:40 | Exhibit section 7 | Scroll the limits section | **What it does not prove is written down: simulated, fees excluded, no order signed.** |

---

## Narration (American English, ~140 words — use this text verbatim if you record voice)

> An autonomous agent made 113 market decisions. Here is the question that actually matters: can
> anyone else check them?
>
> This is Verdict Desk. Break one character of the record and the chain fails — in your own browser,
> not on my server. Restore it and it verifies again.
>
> Every decision is frozen, argued, and ruled on. The lab shows which single argument decided the
> verdict: remove it and the outcome changes. Move the inputs and the rule that fires is named.
>
> This is one decision as a document. Here is what the agent saw. Here is every claim, next to the
> evidence text it cites. Here is the claim that was refused, and why. Here is the argument that
> decided it. And here is the hash, still matching the one written on Ethereum Sepolia.
>
> All 113 verdicts re-derive from their frozen evidence. And what this record does not prove is
> written on the last page, because a system that only advertises is a brochure.

---

## Recording recipes

```bash
# 1280x800, 30fps, no audio
ffmpeg -f x11grab -video_size 1280x800 -framerate 30 -i :0.0 -c:v libx264 -preset veryfast -crf 23 demo-v4.mp4

# compress for GitHub Pages, keep it small
ffmpeg -i demo-v4.mp4 -vf "scale=1280:-2" -c:v libx264 -crf 28 -preset slow -movflags +faststart web/demo/verdict-desk-demo-v4.mp4
```

Publish by committing the file to `web/demo/`; the Pages job serves it at
`https://andriyamaro.github.io/verdict-desk/demo/verdict-desk-demo-v4.mp4`. Paste that URL into the
DoraHacks demo-video field.

Note: desktop capture on this host has produced black frames before (XWayland). If `x11grab` gives
you a black file, record with OBS or with the browser's own capture instead, and check the first
frame before recording the whole thing.

---

## Checklist

- [x] 271 tests green, replay 113/113
- [x] Live ledger, lab, and exhibits published on Pages
- [x] CRE simulation recorded against the live head; anchor transaction on Sepolia
- [x] Submission text updated (`SUBMISSAO_DORAHACKS.md`)
- [ ] Video recorded (yours)
- [ ] DoraHacks build page: description, video, links (yours)
- [ ] **Submission approval chased** — the build is still absent from the public list of 7

---

## Do not do this

- **Do not record a dry run.** See the note at the top.
- **Do not skip shot 2.** Breaking the chain is the most persuasive 13 seconds in the video.
- **Do not cut shot 10.** The limits section is why a legal reviewer trusts the other nine.
