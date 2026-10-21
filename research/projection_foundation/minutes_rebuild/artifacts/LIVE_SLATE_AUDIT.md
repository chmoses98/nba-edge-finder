# Live-slate audit of the joint rotation model (research shadow)

Feed generated 2026-10-20T21:33:24Z (model pf-1.2.1+295b98b); 26 teams, 13 games, 448 players. JRM = candidate; frozen = the engine currently publishing. Minutes are conditional on playing. 'adj' = the conservation correction JRM applied to its own raw scenario sum.

## Team totals

| team | start (UTC) | roster | Σp frozen | Σp JRM | frozen Σp·m raw | frozen after gate | JRM raw | JRM final | JRM adj (min) | frozen gate scale |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| NOP | 10-22T00:00 | 18 | 15.8 | 11.9 | 342.0 | 243.6 | 265.4 | 241.5 | -23.9 | 0.706 |
| HOU | 10-22T00:30 | 17 | 14.6 | 12.1 | 315.9 | 243.2 | 269.3 | 241.5 | -27.8 | 0.764 |
| MIL | 10-21T23:00 | 17 | 15.0 | 11.7 | 306.3 | 243.3 | 243.3 | 241.5 | -1.8 | 0.788 |
| BKN | 10-21T23:30 | 18 | 15.5 | 11.8 | 302.8 | 243.2 | 264.8 | 241.5 | -23.3 | 0.798 |
| NYK | 10-20T23:00 | 17 | 14.7 | 10.9 | 300.8 | 243.3 | 245.0 | 241.5 | -3.5 | 0.803 |
| MEM | 10-22T00:00 | 18 | 14.3 | 11.9 | 290.0 | 243.6 | 254.8 | 241.5 | -13.3 | 0.833 |
| WAS | 10-21T23:00 | 18 | 13.3 | 11.7 | 289.7 | 243.6 | 262.0 | 241.5 | -20.5 | 0.834 |
| ATL | 10-21T23:00 | 18 | 13.2 | 10.8 | 287.2 | 243.0 | 249.9 | 241.5 | -8.4 | 0.841 |
| MIN | 10-21T23:30 | 16 | 12.8 | 11.2 | 287.1 | 243.2 | 245.9 | 241.5 | -4.4 | 0.841 |
| PHI | 10-20T23:00 | 17 | 12.1 | 11.1 | 286.5 | 243.2 | 257.6 | 241.5 | -16.1 | 0.843 |
| SAS | 10-21T01:30 | 17 | 13.1 | 11.6 | 276.8 | 243.2 | 252.3 | 241.5 | -10.8 | 0.872 |
| IND | 10-22T00:00 | 17 | 12.3 | 11.1 | 276.6 | 243.3 | 260.9 | 241.5 | -19.4 | 0.873 |
| PHX | 10-22T02:00 | 17 | 12.8 | 11.7 | 271.6 | 271.6 | 256.9 | 241.5 | -15.4 | 0.889 |
| MIA | 10-21T23:30 | 17 | 13.7 | 11.7 | 268.4 | 268.4 | 247.6 | 241.5 | -6.1 | 1.000 |
| UTA | 10-22T00:00 | 18 | 12.3 | 11.5 | 265.5 | 265.5 | 269.4 | 241.5 | -27.9 | 1.000 |
| DAL | 10-22T00:30 | 17 | 12.9 | 11.5 | 265.4 | 265.4 | 257.5 | 241.5 | -16.0 | 1.000 |
| TOR | 10-21T23:30 | 16 | 13.1 | 11.6 | 263.5 | 263.5 | 244.6 | 241.5 | -3.1 | 1.000 |
| LAL | 10-22T02:00 | 18 | 13.3 | 10.9 | 259.9 | 259.9 | 234.5 | 241.5 | +7.0 | 1.000 |
| CHI | 10-21T23:30 | 17 | 12.6 | 11.1 | 256.6 | 256.6 | 241.2 | 241.5 | +0.3 | 1.000 |
| GSW | 10-22T02:00 | 18 | 12.3 | 11.5 | 242.8 | 242.8 | 244.4 | 241.5 | -2.9 | 1.000 |
| ORL | 10-21T23:00 | 17 | 11.1 | 11.3 | 239.0 | 239.0 | 262.6 | 241.5 | -21.1 | 1.000 |
| POR | 10-22T02:00 | 17 | 10.6 | 10.2 | 237.4 | 237.4 | 224.9 | 241.5 | +16.6 | 1.000 |
| OKC | 10-21T01:30 | 17 | 11.9 | 11.2 | 230.6 | 230.6 | 241.2 | 241.5 | +0.3 | 1.000 |
| CHA | 10-21T23:30 | 17 | 11.2 | 10.8 | 227.2 | 227.2 | 224.5 | 241.5 | +17.0 | 1.000 |
| SAC | 10-22T02:30 | 16 | 9.8 | 10.5 | 218.0 | 218.0 | 241.6 | 241.5 | -0.1 | 1.000 |
| LAC | 10-22T02:30 | 18 | 9.9 | 10.6 | 177.3 | 242.7 | 211.7 | 241.5 | +29.8 | 1.362 |

Mean: frozen raw 268.7, frozen after gate 246.5, JRM raw 249.0 (|adj| mean 13.0, max 29.8), JRM final 241.5. Historical opener raw SD is 17 min, in-season 5.7 (artifacts/MINUTES_COMPARISON.md); live raw SD 14.4.

## Rotation, minutes and probabilities by team (players with p ≥ 0.05, ordered by JRM conditional minutes)

### ATL vs ORL — 2026-10-21T23:00:00Z — Σ(p·min) JRM 241.5 (raw 249.9), frozen 287.2 raw / 243.0 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Jalen Johnson | LIKELY_ACTIVE/ACTIVE | 0.99 | 1.00 | 28.5 | 32.4 [26–39] | +3.8 | -1.3 | 254 |
| Nickeil Alexander-Walker | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 27.6 | 32.4 [26–39] | +4.7 | -0.3 | 459 |
| Dyson Daniels | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 26.4 | 29.4 [22–37] | +3.1 | -1.7 | 271 |
| Onyeka Okongwu | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 24.9 | 29.1 [22–36] | +4.1 | -0.4 | 381 |
| CJ McCollum | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 24.1 | 28.5 [21–36] | +4.4 | -0.0 | 452 |
| Luguentz Dort | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.89 | 20.3 | 20.0 [12–28] | -0.2 | -3.9 | 433 |
| Jock Landale | LIKELY_ACTIVE/ACTIVE | 0.88 | 0.82 | 16.9 | 18.8 [11–28] | +1.9 | -1.2 | 288 |
| Jalen Wilson | UNCERTAIN/QUESTIONABLE | 0.80 | 0.78 | 14.2 | 17.0 [9–26] | +2.8 | +0.2 | 175 |
| Aaron Wiggins | LIKELY_ACTIVE/ACTIVE | 0.88 | 0.82 | 14.7 | 16.6 [8–25] | +1.8 | -0.8 | 339 |
| Corey Kispert | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.68 | 13.2 | 14.4 [5–24] | +1.3 | -1.1 | 350 |
| Kingston Flemings ⚑ | LIKELY_ACTIVE/ACTIVE | 0.66 | 0.53 | 10.0 | 12.6 [3–22] | +2.6 | +0.8 | 0 |
| Zuby Ejiofor ⚑ | LIKELY_ACTIVE/ACTIVE | 0.66 | 0.45 | 9.8 | 11.8 [5–21] | +2.0 | +0.2 | 0 |
| Keshon Gilbert | UNCERTAIN/QUESTIONABLE | 0.70 | 0.28 | 12.7 | 11.7 [5–21] | -1.0 | -3.3 | 4 |
| Asa Newell | LIKELY_ACTIVE/ACTIVE | 0.63 | 0.46 | 11.2 | 11.0 [4–20] | -0.2 | -2.3 | 43 |
| Dorian Finney-Smith | LIKELY_ACTIVE/ACTIVE | 0.79 | 0.08 | 12.9 | 10.7 [4–20] | -2.2 | -4.6 | 445 |

### BKN vs CHA — 2026-10-21T23:30:00Z — Σ(p·min) JRM 241.5 (raw 264.8), frozen 302.8 raw / 243.2 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Michael Porter Jr. | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 25.6 | 30.2 [23–37] | +4.6 | -1.7 | 397 |
| Julius Randle | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.98 | 25.2 | 29.6 [22–37] | +4.4 | -1.7 | 478 |
| Egor Demin | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.96 | 18.7 | 24.5 [17–32] | +5.8 | +1.2 | 52 |
| Noah Clowney | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.95 | 18.2 | 23.9 [17–32] | +5.7 | +1.3 | 135 |
| Terance Mann | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.90 | 17.4 | 21.4 [14–30] | +4.0 | -0.3 | 464 |
| Danny Wolf | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.56 | 15.7 | 19.5 [11–28] | +3.8 | +0.0 | 57 |
| Keon Ellis | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.85 | 15.2 | 18.7 [11–27] | +3.6 | -0.1 | 224 |
| Josh Minott | LIKELY_ACTIVE/ACTIVE | 0.88 | 0.83 | 14.6 | 18.5 [10–27] | +3.9 | +0.4 | 139 |
| Nolan Traore | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.82 | 15.5 | 18.1 [10–27] | +2.6 | -1.2 | 56 |
| Drake Powell | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.92 | 15.9 | 18.1 [10–27] | +2.1 | -1.8 | 63 |
| Ben Saraf | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.82 | 14.6 | 17.3 [9–26] | +2.8 | -0.8 | 44 |
| Day'Ron Sharpe | LIKELY_ACTIVE/ACTIVE | 0.88 | 0.32 | 15.5 | 14.8 [6–24] | -0.7 | -4.5 | 252 |
| Chaney Johnson | LIKELY_ACTIVE/ACTIVE | 0.88 | 0.62 | 11.2 | 13.4 [4–23] | +2.2 | -0.6 | 17 |
| Joshua Jefferson ⚑ | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.62 | 11.3 | 12.7 [4–22] | +1.5 | -1.3 | 0 |
| Mikel Brown Jr. ⚑ | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.62 | 11.3 | 12.7 [4–22] | +1.4 | -1.3 | 0 |

### CHA vs BKN — 2026-10-21T23:30:00Z — Σ(p·min) JRM 241.5 (raw 224.5), frozen 227.2 raw / 227.2 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Brandon Miller | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 29.8 | 32.7 [27–38] | +2.9 | +2.9 | 166 |
| Grayson Allen | UNCERTAIN/QUESTIONABLE | 0.87 | 0.97 | 23.9 | 27.0 [20–34] | +3.1 | +3.1 | 416 |
| Naz Reid | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.96 | 23.4 | 25.6 [18–33] | +2.3 | +2.3 | 483 |
| Moussa Diabate | UNCERTAIN/QUESTIONABLE | 0.96 | 0.97 | 23.7 | 24.8 [17–32] | +1.1 | +1.1 | 176 |
| Royce O'Neale | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.97 | 23.5 | 23.1 [16–31] | -0.4 | -0.4 | 527 |
| Sion James | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.89 | 22.2 | 23.0 [15–31] | +0.9 | +0.9 | 82 |
| Dennis Schroder | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.84 | 21.1 | 21.8 [14–30] | +0.7 | +0.7 | 481 |
| Ryan Kalkbrenner | LIKELY_ACTIVE/ACTIVE | 0.93 | 0.90 | 20.8 | 21.2 [14–29] | +0.5 | +0.5 | 69 |
| Christian Anderson ⚑ | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.68 | 13.4 | 18.5 [10–27] | +5.1 | +5.1 | 0 |
| Hannes Steinbach ⚑ | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.68 | 12.0 | 18.0 [10–27] | +6.0 | +6.0 | 0 |
| Tidjane Salaun | LIKELY_ACTIVE/ACTIVE | 0.65 | 0.64 | 14.6 | 16.6 [8–25] | +2.0 | +2.0 | 97 |
| Liam McNeeley | LIKELY_ACTIVE/ACTIVE | 0.58 | 0.48 | 14.4 | 14.2 [5–23] | -0.2 | -0.2 | 31 |
| PJ Hall | LIKELY_ACTIVE/ACTIVE | 0.86 | 0.79 | 13.1 | 13.7 [5–23] | +0.6 | +0.6 | 36 |

### CHI vs TOR — 2026-10-21T23:30:00Z — Σ(p·min) JRM 241.5 (raw 241.2), frozen 256.6 raw / 256.6 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Matas Buzelis | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 30.1 | 30.5 [24–37] | +0.4 | +0.4 | 157 |
| Josh Giddey | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 29.6 | 30.3 [24–37] | +0.6 | +0.6 | 334 |
| Tre Jones | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.98 | 25.8 | 26.5 [19–34] | +0.8 | +0.8 | 362 |
| Norman Powell | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.97 | 24.6 | 25.6 [18–33] | +0.9 | +0.9 | 420 |
| Isaac Okoro | LIKELY_ACTIVE/PROBABLE | 1.00 | 0.99 | 25.9 | 25.1 [18–33] | -0.8 | -0.8 | 397 |
| Patrick Williams | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.95 | 19.5 | 21.2 [14–29] | +1.6 | +1.6 | 348 |
| Jalen Smith | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.89 | 21.1 | 20.9 [13–29] | -0.2 | -0.2 | 323 |
| Leonard Miller | LIKELY_ACTIVE/PROBABLE | 0.99 | 0.94 | 19.2 | 20.6 [13–29] | +1.4 | +1.4 | 76 |
| Zach Collins | LIKELY_ACTIVE/PROBABLE | 0.92 | 0.63 | 16.5 | 16.2 [7–25] | -0.4 | -0.4 | 245 |
| Buddy Hield | LIKELY_ACTIVE/ACTIVE | 0.71 | 0.39 | 13.4 | 15.0 [6–24] | +1.5 | +1.5 | 522 |
| Tobe Awaka ⚑ | LIKELY_ACTIVE/PROBABLE | 0.92 | 0.70 | 14.3 | 14.2 [5–23] | -0.1 | -0.1 | 0 |
| Caleb Wilson ⚑ | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.67 | 14.3 | 13.9 [5–23] | -0.4 | -0.4 | 0 |
| Jaylin Sellers ⚑ | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.65 | 14.0 | 13.7 [5–23] | -0.3 | -0.3 | 0 |
| Noa Essengue ⚑ | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.34 | 8.5 | 7.9 [1–17] | -0.6 | -0.6 | 2 |

### DAL vs HOU — 2026-10-22T00:30:00Z — Σ(p·min) JRM 241.5 (raw 257.5), frozen 265.4 raw / 265.4 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Cooper Flagg | UNVERIFIED | 0.63 | 0.84 | 32.0 | 30.7 [24–37] | -1.3 | -1.3 | 70 |
| Naji Marshall | UNVERIFIED | 0.94 | 0.95 | 28.2 | 28.2 [21–35] | -0.1 | -0.1 | 371 |
| Kyrie Irving | UNVERIFIED | 0.96 | 0.94 | 30.7 | 27.7 [20–35] | -3.0 | -3.0 | 271 |
| P.J. Washington | UNVERIFIED | 0.94 | 0.96 | 28.4 | 27.5 [20–35] | -0.8 | -0.8 | 446 |
| Max Christie | UNVERIFIED | 0.93 | 0.95 | 26.1 | 25.6 [18–33] | -0.4 | -0.4 | 262 |
| Santi Aldama | UNCERTAIN/QUESTIONABLE | 0.91 | 0.90 | 24.5 | 24.2 [17–32] | -0.3 | -0.3 | 278 |
| Daniel Gafford | UNVERIFIED | 0.88 | 0.88 | 19.7 | 22.0 [14–30] | +2.2 | +2.2 | 433 |
| Zaccharie Risacher | UNVERIFIED | 0.74 | 0.79 | 17.5 | 18.8 [11–28] | +1.2 | +1.2 | 142 |
| Sergio de Larrea ⚑ | UNVERIFIED | 0.61 | 0.69 | 14.8 | 14.4 [5–23] | -0.5 | -0.5 | 0 |
| Tarik Biberovic ⚑ | UNCERTAIN/QUESTIONABLE | 0.51 | 0.68 | 14.8 | 13.7 [5–23] | -1.1 | -1.1 | 0 |
| Moussa Cisse | UNVERIFIED | 0.80 | 0.76 | 14.9 | 13.5 [4–23] | -1.4 | -1.4 | 37 |
| Tobi Lawal ⚑ | UNVERIFIED | 0.61 | 0.66 | 14.8 | 13.4 [4–22] | -1.4 | -1.4 | 0 |
| Morez Johnson Jr. ⚑ | UNVERIFIED | 0.61 | 0.63 | 14.8 | 13.1 [4–22] | -1.8 | -1.8 | 0 |
| Caleb Martin | UNVERIFIED | 0.77 | 0.08 | 13.5 | 12.6 [4–22] | -0.9 | -0.9 | 369 |
| Jett Howard | UNCERTAIN/QUESTIONABLE | 0.67 | 0.29 | 13.6 | 12.3 [3–21] | -1.3 | -1.3 | 133 |
| Marcus Sasser | UNVERIFIED | 0.66 | 0.45 | 13.0 | 10.2 [3–20] | -2.7 | -2.7 | 166 |

### GSW vs LAL — 2026-10-22T02:00:00Z — Σ(p·min) JRM 241.5 (raw 244.4), frozen 242.8 raw / 242.8 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Stephen Curry | UNCERTAIN/QUESTIONABLE | 0.94 | 0.97 | 29.8 | 29.3 [22–37] | -0.6 | -0.6 | 375 |
| Brandin Podziemski | UNCERTAIN/QUESTIONABLE | 0.97 | 0.98 | 28.1 | 28.6 [21–36] | +0.6 | +0.6 | 219 |
| Brandon Williams | UNVERIFIED | 0.94 | 0.94 | 20.5 | 25.1 [18–33] | +4.6 | +4.6 | 139 |
| Draymond Green | UNVERIFIED | 0.95 | 0.96 | 24.8 | 24.9 [18–33] | +0.1 | +0.1 | 415 |
| Gui Santos | UNVERIFIED | 0.96 | 0.94 | 22.0 | 23.6 [16–31] | +1.6 | +1.6 | 147 |
| Al Horford | UNVERIFIED | 0.91 | 0.92 | 22.2 | 22.8 [15–31] | +0.5 | +0.5 | 397 |
| De'Anthony Melton | UNVERIFIED | 0.93 | 0.94 | 22.2 | 22.1 [15–30] | -0.0 | -0.0 | 355 |
| Gary Payton II | UNVERIFIED | 0.76 | 0.85 | 16.9 | 18.9 [11–28] | +2.0 | +2.0 | 305 |
| LJ Cryer | UNVERIFIED | 0.77 | 0.83 | 15.4 | 17.6 [9–26] | +2.2 | +2.2 | 18 |
| Will Richard | UNVERIFIED | 0.81 | 0.62 | 16.6 | 16.7 [9–25] | +0.1 | +0.1 | 69 |
| Georges Niang | UNVERIFIED | 0.64 | 0.15 | 16.3 | 14.7 [6–24] | -1.6 | -1.6 | 453 |
| Graham Ike ⚑ | UNVERIFIED | 0.59 | 0.66 | 12.9 | 13.0 [4–22] | +0.0 | +0.0 | 0 |
| Charles Bassey | UNCERTAIN/QUESTIONABLE | 0.71 | 0.42 | 13.1 | 13.0 [4–22] | -0.1 | -0.1 | 124 |
| Malevy Leons | UNVERIFIED | 0.80 | 0.61 | 11.8 | 12.7 [4–22] | +0.9 | +0.9 | 31 |
| Yaxel Lendeborg ⚑ | UNVERIFIED | 0.59 | 0.65 | 12.9 | 12.6 [4–22] | -0.3 | -0.3 | 0 |

### HOU vs DAL — 2026-10-22T00:30:00Z — Σ(p·min) JRM 241.5 (raw 269.3), frozen 315.9 raw / 243.2 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Kevin Durant | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 26.7 | 30.3 [24–37] | +3.6 | -4.4 | 352 |
| Amen Thompson | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 26.2 | 29.5 [22–37] | +3.4 | -4.5 | 210 |
| Jabari Smith Jr. | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 25.5 | 28.7 [21–36] | +3.2 | -4.4 | 289 |
| Alperen Sengun | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 24.9 | 27.8 [21–35] | +2.9 | -4.5 | 358 |
| Fred VanVleet | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 22.5 | 23.0 [15–31] | +0.5 | -6.2 | 373 |
| Reed Sheppard | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 17.6 | 20.2 [13–28] | +2.6 | -2.7 | 134 |
| Marcus Smart | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.97 | 18.8 | 19.9 [12–28] | +1.0 | -4.6 | 356 |
| Tari Eason | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.96 | 16.8 | 18.9 [11–28] | +2.1 | -2.9 | 221 |
| Steven Adams | UNCERTAIN/QUESTIONABLE | 0.84 | 0.83 | 15.1 | 15.4 [6–24] | +0.3 | -4.2 | 327 |
| Oscar Tshiebwe | LIKELY_ACTIVE/ACTIVE | 0.76 | 0.76 | 10.8 | 12.0 [5–21] | +1.2 | -2.0 | 50 |
| Bruce Thornton ⚑ | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.69 | 8.5 | 9.6 [3–19] | +1.1 | -1.4 | 0 |
| Quadir Copeland ⚑ | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.68 | 8.5 | 9.3 [2–19] | +0.8 | -1.7 | 0 |
| Clint Capela | LIKELY_ACTIVE/ACTIVE | 0.93 | 0.75 | 9.9 | 8.8 [2–18] | -1.1 | -4.1 | 444 |
| Bogdan Bogdanovic | LIKELY_ACTIVE/ACTIVE | 0.71 | 0.14 | 11.3 | 8.4 [1–18] | -2.9 | -6.3 | 378 |
| Jae'Sean Tate | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.40 | 9.0 | 7.6 [1–17] | -1.5 | -4.2 | 341 |

### IND vs NOP — 2026-10-22T00:00:00Z — Σ(p·min) JRM 241.5 (raw 260.9), frozen 276.6 raw / 243.3 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Pascal Siakam | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.98 | 27.6 | 30.7 [24–37] | +3.1 | -0.7 | 475 |
| Tyrese Haliburton | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.98 | 24.5 | 29.0 [22–36] | +4.4 | +1.1 | 334 |
| Andrew Nembhard | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.99 | 26.0 | 28.4 [21–36] | +2.4 | -1.2 | 264 |
| Kelly Oubre Jr. | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.96 | 23.2 | 25.1 [18–33] | +1.9 | -1.2 | 413 |
| Ivica Zubac | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.96 | 22.3 | 24.3 [17–32] | +2.1 | -1.0 | 491 |
| Jarace Walker | UNCERTAIN/QUESTIONABLE | 0.94 | 0.96 | 21.4 | 23.8 [17–31] | +2.4 | -0.5 | 184 |
| Jay Huff | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.85 | 17.5 | 17.8 [10–27] | +0.3 | -2.1 | 176 |
| Ben Sheppard | LIKELY_ACTIVE/ACTIVE | 0.87 | 0.80 | 16.3 | 17.0 [9–26] | +0.7 | -1.5 | 185 |
| Quenton Jackson | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.83 | 16.8 | 17.0 [9–26] | +0.2 | -2.1 | 89 |
| Kobe Brown | LIKELY_ACTIVE/PROBABLE | 0.99 | 0.88 | 17.3 | 16.0 [7–25] | -1.2 | -3.6 | 141 |
| Jalen Slawson | LIKELY_ACTIVE/PROBABLE | 0.98 | 0.69 | 14.1 | 15.5 [6–25] | +1.3 | -0.6 | 24 |
| Obi Toppin | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.77 | 16.2 | 14.7 [6–24] | -1.5 | -3.7 | 387 |
| Larry Nance Jr. | LIKELY_ACTIVE/ACTIVE | 0.76 | 0.43 | 12.6 | 12.1 [5–22] | -0.4 | -2.2 | 322 |

### LAC vs SAC — 2026-10-22T02:30:00Z — Σ(p·min) JRM 241.5 (raw 211.7), frozen 177.3 raw / 242.7 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Darius Garland | UNVERIFIED | 0.96 | 0.99 | 38.2 | 32.4 [26–39] | -5.8 | +4.5 | 427 |
| Rui Hachimura | UNVERIFIED | 0.90 | 0.98 | 31.8 | 27.1 [20–34] | -4.8 | +3.8 | 406 |
| Derrick Jones Jr. | UNVERIFIED | 0.97 | 0.98 | 33.2 | 26.3 [19–34] | -6.9 | +2.0 | 433 |
| Kris Dunn | UNVERIFIED | 0.98 | 0.99 | 31.3 | 25.0 [18–33] | -6.3 | +2.1 | 311 |
| Brook Lopez | UNVERIFIED | 0.98 | 0.99 | 31.1 | 24.6 [17–32] | -6.5 | +1.9 | 464 |
| Kobe Sanders | UNVERIFIED | 0.81 | 0.89 | 22.8 | 22.4 [15–31] | -0.4 | +5.8 | 68 |
| Jalen Pickett | UNVERIFIED | 0.62 | 0.75 | 20.4 | 22.4 [15–31] | +2.0 | +7.5 | 124 |
| Isaiah Jackson | UNVERIFIED | 0.61 | 0.83 | 20.8 | 21.2 [14–29] | +0.4 | +6.0 | 217 |
| Baba Miller ⚑ | UNVERIFIED | 0.61 | 0.67 | 14.4 | 19.5 [11–28] | +5.1 | +9.0 | 0 |
| Keaton Wagler ⚑ | UNVERIFIED | 0.61 | 0.68 | 14.6 | 18.5 [10–27] | +3.9 | +7.9 | 0 |
| Nick Martinelli ⚑ | UNVERIFIED | 0.61 | 0.67 | 14.4 | 18.2 [10–27] | +3.8 | +7.7 | 0 |
| Gradey Dick | UNVERIFIED | 0.55 | 0.67 | 13.6 | 15.2 [6–24] | +1.6 | +5.3 | 190 |
| Cam Christie | UNVERIFIED | 0.68 | 0.53 | 9.4 | 9.4 [2–19] | +0.1 | +2.6 | 66 |

### LAL vs GSW — 2026-10-22T02:00:00Z — Σ(p·min) JRM 241.5 (raw 234.5), frozen 259.9 raw / 259.9 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Luka Doncic | UNVERIFIED | 0.96 | 0.96 | 34.1 | 33.6 [27–39] | -0.5 | -0.5 | 442 |
| Austin Reaves | UNVERIFIED | 0.96 | 0.96 | 32.4 | 33.4 [27–39] | +1.0 | +1.0 | 332 |
| Walker Kessler | UNVERIFIED | 0.90 | 0.95 | 26.4 | 26.6 [19–34] | +0.1 | +0.1 | 201 |
| Quentin Grimes | UNVERIFIED | 0.91 | 0.97 | 22.1 | 24.2 [17–32] | +2.1 | +2.1 | 314 |
| Collin Sexton | UNCERTAIN/QUESTIONABLE | 0.86 | 0.95 | 22.5 | 23.3 [16–32] | +0.8 | +0.8 | 393 |
| Ziaire Williams | UNVERIFIED | 0.93 | 0.88 | 20.0 | 21.4 [14–30] | +1.3 | +1.3 | 267 |
| Sandro Mamukelashvili | UNVERIFIED | 0.88 | 0.85 | 21.1 | 21.3 [14–29] | +0.2 | +0.2 | 268 |
| Jake LaRavia | UNVERIFIED | 0.97 | 0.96 | 22.6 | 21.1 [13–29] | -1.5 | -1.5 | 218 |
| Jaden Hardy | UNVERIFIED | 0.78 | 0.66 | 17.8 | 18.8 [11–27] | +1.0 | +1.0 | 234 |
| Matisse Thybulle | UNVERIFIED | 0.52 | 0.36 | 17.0 | 16.8 [9–26] | -0.2 | -0.2 | 374 |
| Kevon Looney | UNVERIFIED | 0.74 | 0.38 | 11.9 | 14.7 [6–24] | +2.8 | +2.8 | 416 |
| AK Okereke ⚑ | UNVERIFIED | 0.59 | 0.60 | 10.8 | 13.2 [4–22] | +2.4 | +2.4 | 0 |
| Cameron Carr ⚑ | UNCERTAIN/QUESTIONABLE | 0.49 | 0.58 | 10.9 | 12.4 [3–22] | +1.5 | +1.5 | 0 |
| Arthur Kaluma ⚑ | UNVERIFIED | 0.59 | 0.57 | 10.8 | 12.3 [3–21] | +1.5 | +1.5 | 0 |
| Jarred Vanderbilt | UNCERTAIN/QUESTIONABLE | 0.69 | 0.20 | 13.7 | 12.1 [5–22] | -1.7 | -1.7 | 358 |

### MEM vs UTA — 2026-10-22T00:00:00Z — Σ(p·min) JRM 241.5 (raw 254.8), frozen 290.0 raw / 243.6 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Jerami Grant | UNCERTAIN/QUESTIONABLE | 0.96 | 0.97 | 23.5 | 26.8 [20–34] | +3.3 | -1.2 | 393 |
| Zach Edey | UNVERIFIED | 0.95 | 0.89 | 19.4 | 24.1 [17–32] | +4.7 | +1.0 | 77 |
| Jaylen Wells | UNVERIFIED | 0.95 | 0.32 | 20.8 | 23.6 [16–31] | +2.9 | -1.1 | 148 |
| Ty Jerome | UNVERIFIED | 0.93 | 0.89 | 17.8 | 23.3 [16–32] | +5.6 | +2.2 | 244 |
| GG Jackson | UNCERTAIN/QUESTIONABLE | 0.85 | 0.91 | 18.6 | 22.6 [15–31] | +3.9 | +0.4 | 131 |
| Cedric Coward | UNVERIFIED | 0.88 | 0.93 | 20.2 | 21.8 [14–30] | +1.6 | -2.3 | 62 |
| Taylor Hendricks | UNVERIFIED | 0.94 | 0.92 | 17.9 | 20.6 [13–29] | +2.7 | -0.7 | 102 |
| Cam Spencer | UNVERIFIED | 0.83 | 0.86 | 17.7 | 20.5 [13–29] | +2.8 | -0.6 | 97 |
| Jahmai Mashack | UNVERIFIED | 0.92 | 0.94 | 16.3 | 20.5 [13–29] | +4.2 | +1.0 | 30 |
| Javon Small | UNVERIFIED | 0.93 | 0.91 | 16.2 | 19.2 [11–28] | +2.9 | -0.2 | 40 |
| Kris Murray | UNVERIFIED | 0.78 | 0.86 | 16.5 | 19.1 [11–28] | +2.6 | -0.6 | 188 |
| Olivier-Maxence Prosper | UNVERIFIED | 0.87 | 0.49 | 17.7 | 18.1 [10–27] | +0.4 | -2.9 | 142 |
| Karim Lopez ⚑ | UNVERIFIED | 0.58 | 0.67 | 9.5 | 13.1 [4–22] | +3.6 | +1.8 | 0 |
| Carson Cooper ⚑ | UNVERIFIED | 0.58 | 0.65 | 9.6 | 12.7 [4–22] | +3.2 | +1.3 | 0 |
| Cameron Boozer ⚑ | UNVERIFIED | 0.58 | 0.63 | 9.5 | 12.6 [3–22] | +3.1 | +1.3 | 0 |

### MIA vs MIN — 2026-10-21T23:30:00Z — Σ(p·min) JRM 241.5 (raw 247.6), frozen 268.4 raw / 268.4 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Bam Adebayo | UNCERTAIN/QUESTIONABLE | 0.98 | 0.98 | 32.4 | 31.2 [24–38] | -1.2 | -1.2 | 489 |
| Andrew Wiggins | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 27.9 | 27.0 [20–34] | -0.8 | -0.8 | 434 |
| Giannis Antetokounmpo | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 27.4 | 26.6 [19–34] | -0.8 | -0.8 | 431 |
| Davion Mitchell | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 25.6 | 25.1 [18–33] | -0.5 | -0.5 | 370 |
| Pelle Larsson | UNCERTAIN/QUESTIONABLE | 0.93 | 0.97 | 23.5 | 24.1 [17–32] | +0.7 | +0.7 | 124 |
| Bobby Portis | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.94 | 22.4 | 22.8 [15–31] | +0.5 | +0.5 | 473 |
| Tim Hardaway Jr. | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.97 | 22.1 | 19.5 [11–28] | -2.6 | -2.6 | 490 |
| Klay Thompson | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.89 | 19.0 | 18.8 [11–28] | -0.2 | -0.2 | 319 |
| Simone Fontecchio | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.87 | 15.0 | 16.7 [9–25] | +1.7 | +1.7 | 262 |
| Nick Richards | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.81 | 17.8 | 16.3 [7–25] | -1.5 | -1.5 | 303 |
| Keshad Johnson | LIKELY_ACTIVE/ACTIVE | 0.69 | 0.62 | 11.0 | 11.8 [5–21] | +0.8 | +0.8 | 48 |
| Ryan Conwell ⚑ | LIKELY_ACTIVE/ACTIVE | 0.62 | 0.53 | 11.7 | 10.8 [4–20] | -0.9 | -0.9 | 0 |
| Nikola Jovic | LIKELY_ACTIVE/ACTIVE | 0.67 | 0.18 | 12.3 | 10.8 [4–20] | -1.6 | -1.6 | 152 |
| Dru Smith | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.40 | 10.8 | 10.3 [3–20] | -0.4 | -0.4 | 108 |
| Tre Donaldson ⚑ | LIKELY_ACTIVE/ACTIVE | 0.62 | 0.53 | 11.7 | 10.2 [3–20] | -1.5 | -1.5 | 0 |

### MIL vs WAS — 2026-10-21T23:00:00Z — Σ(p·min) JRM 241.5 (raw 243.3), frozen 306.3 raw / 243.3 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Ryan Rollins | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 24.1 | 29.6 [22–37] | +5.4 | -0.8 | 154 |
| Tyler Herro | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.98 | 23.5 | 26.5 [19–34] | +3.0 | -3.1 | 394 |
| AJ Green | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 20.1 | 24.6 [17–32] | +4.6 | -0.6 | 240 |
| Myles Turner | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.95 | 19.8 | 24.1 [17–32] | +4.3 | -0.9 | 434 |
| Jaime Jaquez Jr. | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.95 | 19.4 | 23.2 [16–31] | +3.8 | -1.3 | 216 |
| Ousmane Dieng | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.98 | 15.4 | 22.0 [14–30] | +6.6 | +2.6 | 166 |
| Kyle Kuzma | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.89 | 18.6 | 19.4 [11–28] | +0.8 | -4.0 | 463 |
| Jericho Sims | UNCERTAIN/QUESTIONABLE | 0.96 | 0.97 | 15.1 | 19.2 [11–28] | +4.0 | +0.1 | 254 |
| Cormac Ryan | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.84 | 15.9 | 19.0 [11–28] | +3.1 | -1.0 | 11 |
| Kel'el Ware | LIKELY_ACTIVE/ACTIVE | 0.90 | 0.83 | 15.0 | 17.9 [10–27] | +2.8 | -1.1 | 141 |
| Bogoljub Markovic ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.60 | 9.4 | 12.6 [4–22] | +3.3 | +0.8 | 0 |
| Brayden Burries ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.59 | 9.4 | 12.4 [3–21] | +2.9 | +0.5 | 0 |
| Nate Ament ⚑ | LIKELY_ACTIVE/PROBABLE | 0.90 | 0.60 | 9.4 | 12.4 [3–21] | +3.0 | +0.5 | 0 |
| Kasparas Jakucionis | LIKELY_ACTIVE/ACTIVE | 0.73 | 0.18 | 12.6 | 12.2 [3–21] | -0.4 | -3.6 | 53 |
| Kam Jones | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.31 | 11.3 | 11.7 [5–21] | +0.4 | -2.5 | 37 |

### MIN vs MIA — 2026-10-21T23:30:00Z — Σ(p·min) JRM 241.5 (raw 245.9), frozen 287.1 raw / 243.2 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Anthony Edwards | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 27.3 | 30.3 [24–37] | +3.0 | -2.0 | 442 |
| Jaden McDaniels | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 26.7 | 30.2 [23–37] | +3.6 | -1.3 | 439 |
| Rudy Gobert | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 25.6 | 28.8 [22–36] | +3.2 | -1.4 | 499 |
| LaMelo Ball | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 22.6 | 26.7 [19–34] | +4.0 | -0.1 | 303 |
| Cody Williams | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.95 | 22.5 | 25.6 [18–33] | +3.1 | -1.0 | 117 |
| Ayo Dosunmu | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.98 | 22.4 | 24.9 [18–33] | +2.5 | -1.5 | 348 |
| Jonathan Kuminga | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.88 | 18.9 | 19.0 [11–28] | +0.1 | -3.3 | 293 |
| Bones Hyland | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.78 | 17.2 | 17.5 [9–26] | +0.3 | -2.8 | 255 |
| Trey Lyles | LIKELY_ACTIVE/ACTIVE | 0.91 | 0.76 | 16.9 | 15.7 [6–25] | -1.2 | -4.3 | 362 |
| Terrence Shannon Jr. | LIKELY_ACTIVE/ACTIVE | 0.89 | 0.74 | 13.8 | 15.6 [6–25] | +1.9 | -0.6 | 75 |
| Isaiah Evans ⚑ | LIKELY_ACTIVE/ACTIVE | 0.62 | 0.54 | 10.6 | 12.5 [3–22] | +1.9 | -0.1 | 0 |
| Jaylen Clark | LIKELY_ACTIVE/ACTIVE | 0.90 | 0.64 | 13.3 | 12.5 [3–22] | -0.8 | -3.3 | 108 |
| Joan Beringer | LIKELY_ACTIVE/ACTIVE | 0.85 | 0.63 | 12.5 | 11.8 [5–21] | -0.8 | -3.0 | 40 |
| Zyon Pullin | LIKELY_ACTIVE/ACTIVE | 0.47 | 0.20 | 9.8 | 7.0 [0–16] | -2.8 | -4.6 | 8 |
| Rocco Zikarsky | UNCERTAIN/QUESTIONABLE | 0.33 | 0.10 | 9.0 | 6.3 [0–16] | -2.8 | -4.4 | 5 |

### NOP vs IND — 2026-10-22T00:00:00Z — Σ(p·min) JRM 241.5 (raw 265.4), frozen 342.0 raw / 243.6 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Trey Murphy III | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 24.1 | 30.6 [24–37] | +6.4 | -3.3 | 317 |
| Saddiq Bey | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 22.0 | 28.5 [21–36] | +6.5 | -2.4 | 364 |
| Zion Williamson | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 21.7 | 27.0 [20–34] | +5.3 | -3.4 | 276 |
| Dejounte Murray | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.98 | 20.1 | 25.0 [18–33] | +4.9 | -3.2 | 398 |
| Jeremiah Fears | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 16.4 | 22.9 [15–31] | +6.6 | -0.1 | 82 |
| Bennedict Mathurin | LIKELY_ACTIVE/ACTIVE | 0.93 | 0.95 | 16.7 | 21.3 [14–29] | +4.6 | -2.2 | 264 |
| Herbert Jones | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.90 | 18.8 | 19.6 [11–28] | +0.7 | -6.9 | 296 |
| Julian Reese | LIKELY_ACTIVE/ACTIVE | 0.93 | 0.92 | 16.6 | 19.1 [11–28] | +2.5 | -4.2 | 13 |
| Derik Queen | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.95 | 15.0 | 18.5 [10–27] | +3.6 | -2.5 | 81 |
| Yves Missi | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.89 | 13.3 | 12.9 [4–22] | -0.4 | -5.8 | 139 |
| Bryce McGowens | LIKELY_ACTIVE/ACTIVE | 0.93 | 0.22 | 14.3 | 12.8 [4–22] | -1.4 | -7.2 | 159 |
| Jordan Poole | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.47 | 14.7 | 12.7 [4–22] | -2.0 | -7.9 | 451 |
| Malik Dia ⚑ | LIKELY_ACTIVE/ACTIVE | 0.73 | 0.65 | 7.6 | 9.9 [3–19] | +2.3 | -0.7 | 0 |
| Jaron Pierre Jr. ⚑ | LIKELY_ACTIVE/ACTIVE | 0.73 | 0.65 | 7.6 | 9.7 [3–19] | +2.2 | -0.9 | 0 |
| AJ Johnson | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.34 | 8.2 | 8.2 [1–18] | -0.0 | -3.4 | 77 |

### NYK vs PHI — 2026-10-20T23:00:00Z — Σ(p·min) JRM 241.5 (raw 245.0), frozen 300.8 raw / 243.3 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Jalen Brunson | LIKELY_ACTIVE/ACTIVE | 0.98 | 1.00 | 28.3 | 33.3 [27–39] | +5.0 | -1.7 | 488 |
| OG Anunoby | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 27.6 | 31.8 [25–38] | +4.1 | -2.4 | 419 |
| Karl-Anthony Towns | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 25.4 | 30.4 [24–37] | +5.0 | -1.0 | 398 |
| Josh Hart | UNCERTAIN/QUESTIONABLE | 0.96 | 0.96 | 21.8 | 27.3 [20–35] | +5.6 | +0.5 | 467 |
| Mikal Bridges | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 23.7 | 27.2 [20–34] | +3.5 | -2.1 | 554 |
| Miles McBride | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.97 | 18.9 | 22.7 [15–31] | +3.8 | -0.6 | 271 |
| Landry Shamet | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.93 | 17.9 | 20.1 [13–28] | +2.2 | -2.0 | 370 |
| Jose Alvarado | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.78 | 14.6 | 17.6 [9–26] | +3.1 | -0.4 | 296 |
| Andre Drummond | LIKELY_ACTIVE/ACTIVE | 0.86 | 0.68 | 14.7 | 15.9 [7–25] | +1.1 | -2.4 | 425 |
| Jordan Clarkson | LIKELY_ACTIVE/ACTIVE | 0.90 | 0.59 | 12.5 | 12.8 [4–22] | +0.3 | -2.6 | 444 |
| Tyler Nickel ⚑ | LIKELY_ACTIVE/ACTIVE | 0.78 | 0.59 | 8.6 | 12.3 [3–21] | +3.6 | +1.6 | 0 |
| Jaden Akins ⚑ | LIKELY_ACTIVE/ACTIVE | 0.78 | 0.51 | 8.6 | 11.3 [4–21] | +2.7 | +0.7 | 0 |
| Mohamed Diawara | LIKELY_ACTIVE/ACTIVE | 0.83 | 0.56 | 9.9 | 10.4 [3–20] | +0.5 | -1.8 | 68 |
| Kevin McCullar Jr. | LIKELY_ACTIVE/ACTIVE | 0.57 | 0.11 | 7.2 | 6.9 [0–16] | -0.3 | -2.0 | 23 |
| Pacome Dadiet | LIKELY_ACTIVE/ACTIVE | 0.63 | 0.22 | 7.3 | 6.0 [0–16] | -1.3 | -3.0 | 46 |

### OKC vs SAS — 2026-10-21T01:30:00Z — Σ(p·min) JRM 241.5 (raw 241.2), frozen 230.6 raw / 230.6 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Shai Gilgeous-Alexander | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 33.6 | 33.9 [28–39] | +0.3 | +0.3 | 449 |
| Chet Holmgren | UNCERTAIN/QUESTIONABLE | 0.98 | 0.97 | 27.3 | 29.1 [22–36] | +1.9 | +1.9 | 183 |
| Jalen Williams | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 26.5 | 28.7 [21–36] | +2.2 | +2.2 | 249 |
| Ajay Mitchell | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.90 | 21.1 | 23.8 [17–32] | +2.8 | +2.8 | 94 |
| Cason Wallace | UNCERTAIN/QUESTIONABLE | 0.86 | 0.92 | 21.9 | 23.3 [16–32] | +1.4 | +1.4 | 228 |
| Isaiah Hartenstein | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.94 | 20.8 | 23.2 [16–31] | +2.4 | +2.4 | 399 |
| Jared McCain | LIKELY_ACTIVE/ACTIVE | 0.91 | 0.92 | 16.8 | 21.8 [14–30] | +5.0 | +5.0 | 90 |
| Kenrich Williams | LIKELY_ACTIVE/ACTIVE | 0.91 | 0.71 | 15.0 | 17.3 [9–26] | +2.3 | +2.3 | 402 |
| Alex Caruso | LIKELY_ACTIVE/ACTIVE | 0.90 | 0.44 | 15.9 | 16.6 [8–25] | +0.7 | +0.7 | 411 |
| Jaylin Williams | UNCERTAIN/QUESTIONABLE | 0.66 | 0.69 | 15.3 | 16.6 [8–25] | +1.3 | +1.3 | 230 |
| Brooks Barnhizer | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.74 | 11.9 | 14.3 [5–23] | +2.4 | +2.4 | 40 |
| Josh Dix ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.68 | 11.4 | 12.5 [3–22] | +1.2 | +1.2 | 0 |
| Aday Mara ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.66 | 11.8 | 12.2 [5–22] | +0.4 | +0.4 | 0 |
| Bennett Stirtz ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.66 | 11.4 | 12.1 [5–22] | +0.7 | +0.7 | 0 |

### ORL vs ATL — 2026-10-21T23:00:00Z — Σ(p·min) JRM 241.5 (raw 262.6), frozen 239.0 raw / 239.0 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Paolo Banchero | LIKELY_ACTIVE/ACTIVE | 0.99 | 1.00 | 32.6 | 31.5 [25–38] | -1.1 | -1.1 | 270 |
| Desmond Bane | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 29.4 | 29.9 [23–36] | +0.4 | +0.4 | 395 |
| Jalen Suggs | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 25.9 | 27.3 [20–35] | +1.4 | +1.4 | 268 |
| Franz Wagner | UNCERTAIN/QUESTIONABLE | 0.94 | 0.97 | 24.0 | 26.9 [20–34] | +2.9 | +2.9 | 324 |
| Wendell Carter Jr. | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 26.7 | 25.8 [19–33] | -0.9 | -0.9 | 417 |
| Nikola Vucevic | LIKELY_ACTIVE/ACTIVE | 0.90 | 0.94 | 22.3 | 21.8 [14–30] | -0.5 | -0.5 | 500 |
| Tristan da Silva | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 23.2 | 21.0 [13–29] | -2.2 | -2.2 | 151 |
| Jevon Carter | LIKELY_ACTIVE/ACTIVE | 0.93 | 0.89 | 17.5 | 16.9 [9–26] | -0.7 | -0.7 | 425 |
| Jamal Cain | LIKELY_ACTIVE/ACTIVE | 0.90 | 0.88 | 15.7 | 15.9 [7–25] | +0.3 | +0.3 | 115 |
| Goga Bitadze | LIKELY_ACTIVE/ACTIVE | 0.89 | 0.86 | 16.7 | 15.5 [6–25] | -1.2 | -1.2 | 381 |
| Colin Castleton | LIKELY_ACTIVE/ACTIVE | 0.62 | 0.67 | 11.0 | 11.2 [4–21] | +0.2 | +0.2 | 45 |
| Jase Richardson | UNCERTAIN/QUESTIONABLE | 0.47 | 0.62 | 7.9 | 10.4 [3–20] | +2.5 | +2.5 | 54 |
| Alex Morales | LIKELY_ACTIVE/ACTIVE | 0.51 | 0.45 | 8.0 | 8.0 [1–17] | +0.0 | +0.0 | 4 |

### PHI vs NYK — 2026-10-20T23:00:00Z — Σ(p·min) JRM 241.5 (raw 257.6), frozen 286.5 raw / 243.2 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Tyrese Maxey | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 30.1 | 31.5 [25–38] | +1.5 | -3.9 | 387 |
| Jaylen Brown | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 29.0 | 31.1 [24–37] | +2.1 | -3.1 | 452 |
| VJ Edgecombe | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 28.5 | 30.8 [24–37] | +2.3 | -2.8 | 75 |
| Joel Embiid | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 27.1 | 30.2 [23–37] | +3.1 | -1.7 | 332 |
| LeBron James | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.98 | 26.4 | 28.5 [21–36] | +2.1 | -2.7 | 425 |
| Rayan Rupert | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.94 | 17.3 | 22.1 [15–30] | +4.8 | +1.7 | 155 |
| Dean Wade | UNCERTAIN/QUESTIONABLE | 0.92 | 0.84 | 17.1 | 17.7 [10–26] | +0.6 | -2.4 | 342 |
| Kentavious Caldwell-Pope | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.86 | 17.4 | 15.7 [6–25] | -1.7 | -4.8 | 493 |
| Anfernee Simons | UNCERTAIN/QUESTIONABLE | 0.55 | 0.53 | 20.3 | 15.4 [6–25] | -4.8 | -8.5 | 424 |
| Adem Bona | UNCERTAIN/QUESTIONABLE | 0.85 | 0.81 | 15.3 | 13.6 [5–23] | -1.6 | -4.3 | 129 |
| Justin Edwards | LIKELY_ACTIVE/ACTIVE | 0.90 | 0.74 | 12.3 | 12.4 [3–21] | +0.1 | -2.1 | 107 |
| Labaron Philon Jr. ⚑ | LIKELY_ACTIVE/ACTIVE | 0.78 | 0.54 | 11.8 | 9.7 [3–19] | -2.1 | -4.2 | 0 |
| Caleb Love | LIKELY_ACTIVE/ACTIVE | 0.63 | 0.59 | 9.4 | 9.6 [3–19] | +0.2 | -1.4 | 49 |
| Jabari Walker | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.29 | 9.0 | 7.7 [1–17] | -1.3 | -2.9 | 251 |

### PHX vs POR — 2026-10-22T02:00:00Z — Σ(p·min) JRM 241.5 (raw 256.9), frozen 271.6 raw / 271.6 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Devin Booker | UNVERIFIED | 0.98 | 0.98 | 34.2 | 33.1 [27–38] | -1.1 | -1.1 | 465 |
| Dillon Brooks | UNVERIFIED | 0.98 | 0.97 | 30.5 | 29.6 [22–37] | -0.9 | -0.9 | 448 |
| Miles Bridges | UNVERIFIED | 0.94 | 0.98 | 27.6 | 26.5 [19–34] | -1.1 | -1.1 | 421 |
| Jalen Green | UNVERIFIED | 0.93 | 0.91 | 27.7 | 25.9 [19–34] | -1.9 | -1.9 | 339 |
| Collin Gillespie | UNVERIFIED | 0.96 | 0.97 | 23.7 | 22.3 [15–31] | -1.4 | -1.4 | 136 |
| Jordan Goodwin | UNVERIFIED | 0.89 | 0.82 | 21.9 | 20.2 [13–28] | -1.7 | -1.7 | 218 |
| Oso Ighodaro | UNCERTAIN/QUESTIONABLE | 0.94 | 0.91 | 21.2 | 19.4 [11–28] | -1.8 | -1.8 | 142 |
| Luke Kennard | UNCERTAIN/QUESTIONABLE | 0.69 | 0.82 | 20.6 | 18.5 [10–27] | -2.1 | -2.1 | 402 |
| Ryan Dunn | UNVERIFIED | 0.89 | 0.89 | 17.8 | 17.6 [9–26] | -0.2 | -0.2 | 142 |
| Pat Spencer | UNVERIFIED | 0.87 | 0.78 | 20.0 | 16.4 [8–25] | -3.6 | -3.6 | 111 |
| Rasheer Fleming | UNVERIFIED | 0.77 | 0.80 | 14.0 | 13.8 [5–23] | -0.2 | -0.2 | 55 |
| Koa Peat ⚑ | UNVERIFIED | 0.47 | 0.60 | 11.4 | 12.9 [4–22] | +1.5 | +1.5 | 0 |
| Jamaree Bouyea | UNVERIFIED | 0.79 | 0.67 | 14.2 | 10.5 [3–20] | -3.7 | -3.7 | 65 |
| Khaman Maluach | UNVERIFIED | 0.72 | 0.39 | 12.4 | 9.7 [3–19] | -2.8 | -2.8 | 46 |
| Drew Timme | UNVERIFIED | 0.37 | 0.17 | 9.9 | 7.4 [0–17] | -2.6 | -2.6 | 35 |

### POR vs PHX — 2026-10-22T02:00:00Z — Σ(p·min) JRM 241.5 (raw 224.9), frozen 237.4 raw / 237.4 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Deni Avdija | UNVERIFIED | 0.98 | 0.99 | 32.7 | 34.1 [28–39] | +1.4 | +1.4 | 425 |
| Toumani Camara | UNVERIFIED | 0.99 | 0.99 | 32.7 | 33.7 [28–39] | +1.0 | +1.0 | 230 |
| Jrue Holiday | UNCERTAIN/QUESTIONABLE | 0.97 | 0.98 | 28.5 | 31.4 [25–38] | +2.9 | +2.9 | 437 |
| Ja Morant | UNVERIFIED | 0.96 | 0.98 | 27.3 | 29.1 [22–36] | +1.8 | +1.8 | 327 |
| Donovan Clingan | UNVERIFIED | 0.98 | 0.98 | 25.6 | 26.0 [19–34] | +0.4 | +0.4 | 144 |
| Scoot Henderson | UNVERIFIED | 0.96 | 0.98 | 23.5 | 24.8 [18–32] | +1.3 | +1.3 | 158 |
| Micah Potter | UNCERTAIN/QUESTIONABLE | 0.70 | 0.76 | 17.1 | 18.2 [10–27] | +1.0 | +1.0 | 111 |
| Robert Williams III | UNVERIFIED | 0.85 | 0.80 | 17.8 | 18.1 [10–27] | +0.4 | +0.4 | 261 |
| Damian Lillard | UNVERIFIED | 0.51 | 0.59 | 29.8 | 18.1 [10–27] | -11.7 | -11.7 | 352 |
| Vit Krejci | UNVERIFIED | 0.46 | 0.43 | 14.2 | 17.7 [10–26] | +3.5 | +3.5 | 202 |
| Branden Carlson | UNVERIFIED | 0.52 | 0.56 | 14.3 | 13.4 [4–22] | -0.9 | -0.9 | 73 |
| John Tonje | UNVERIFIED | 0.29 | 0.34 | 11.4 | 12.5 [3–22] | +1.0 | +1.0 | 5 |
| Sidy Cissoko | UNVERIFIED | 0.58 | 0.46 | 10.5 | 9.7 [3–19] | -0.8 | -0.8 | 106 |
| Chris Youngblood | UNCERTAIN/QUESTIONABLE | 0.25 | 0.23 | 7.1 | 6.8 [0–16] | -0.3 | -0.3 | 32 |
| Yang Hansen | UNVERIFIED | 0.36 | 0.11 | 7.2 | 6.1 [0–16] | -1.1 | -1.1 | 43 |

### SAC vs LAC — 2026-10-22T02:30:00Z — Σ(p·min) JRM 241.5 (raw 241.6), frozen 218.0 raw / 218.0 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Nique Clifford | UNVERIFIED | 0.95 | 0.98 | 26.5 | 29.0 [22–36] | +2.5 | +2.5 | 75 |
| Zach LaVine | UNVERIFIED | 0.94 | 0.84 | 27.0 | 28.3 [21–36] | +1.4 | +1.4 | 400 |
| Domantas Sabonis | UNVERIFIED | 0.95 | 0.96 | 27.3 | 28.1 [21–35] | +0.8 | +0.8 | 436 |
| Keegan Murray | UNVERIFIED | 0.74 | 0.70 | 32.2 | 27.5 [20–35] | -4.7 | -4.7 | 256 |
| Precious Achiuwa | UNVERIFIED | 0.97 | 0.99 | 24.1 | 26.9 [20–34] | +2.8 | +2.8 | 393 |
| De'Andre Hunter | UNVERIFIED | 0.67 | 0.76 | 22.2 | 24.4 [17–32] | +2.2 | +2.2 | 372 |
| Daeqwon Plowden | UNVERIFIED | 0.94 | 0.97 | 22.3 | 23.5 [16–31] | +1.2 | +1.2 | 38 |
| Malik Monk | UNCERTAIN/QUESTIONABLE | 0.73 | 0.87 | 18.7 | 21.6 [14–30] | +2.8 | +2.8 | 449 |
| Leaky Black | UNVERIFIED | 0.53 | 0.76 | 21.9 | 19.7 [12–28] | -2.2 | -2.2 | 41 |
| Emanuel Sharp ⚑ | UNVERIFIED | 0.61 | 0.71 | 14.9 | 16.4 [8–25] | +1.4 | +1.4 | 0 |
| Alex Karaban ⚑ | UNVERIFIED | 0.61 | 0.70 | 14.9 | 16.2 [7–25] | +1.3 | +1.3 | 0 |
| Darius Acuff Jr. ⚑ | UNVERIFIED | 0.61 | 0.71 | 14.9 | 15.8 [7–25] | +0.9 | +0.9 | 0 |
| Jonathan Mogbo | UNVERIFIED | 0.50 | 0.57 | 11.2 | 12.5 [3–22] | +1.3 | +1.3 | 101 |

### SAS vs OKC — 2026-10-21T01:30:00Z — Σ(p·min) JRM 241.5 (raw 252.3), frozen 276.8 raw / 243.2 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Stephon Castle | LIKELY_ACTIVE/ACTIVE | 0.99 | 1.00 | 26.7 | 29.6 [22–37] | +2.9 | -0.7 | 150 |
| De'Aaron Fox | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 27.2 | 28.6 [21–36] | +1.4 | -2.4 | 450 |
| Victor Wembanyama | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 24.6 | 28.5 [21–36] | +3.9 | +0.5 | 182 |
| Devin Vassell | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 25.5 | 26.4 [19–34] | +0.9 | -2.6 | 370 |
| Julian Champagnie | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 22.6 | 24.2 [17–32] | +1.7 | -1.5 | 256 |
| Keldon Johnson | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.93 | 19.7 | 21.7 [14–30] | +2.0 | -0.7 | 453 |
| Dylan Harper | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.94 | 18.7 | 20.1 [12–28] | +1.3 | -1.2 | 70 |
| Harrison Barnes | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.92 | 18.5 | 19.5 [11–28] | +1.0 | -1.5 | 531 |
| Luke Kornet | LIKELY_ACTIVE/ACTIVE | 0.93 | 0.83 | 17.8 | 15.9 [7–25] | -1.9 | -4.4 | 355 |
| Carter Bryant | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.78 | 14.5 | 14.2 [5–23] | -0.3 | -2.4 | 71 |
| Ja'Kobi Gillespie ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.63 | 11.1 | 12.1 [5–22] | +1.0 | -0.6 | 0 |
| Tarris Reed Jr. ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.61 | 10.9 | 11.7 [5–21] | +0.8 | -0.7 | 0 |
| Maliq Brown ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.56 | 10.4 | 11.3 [4–21] | +0.8 | -0.6 | 0 |
| David Jones Garcia | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.17 | 7.3 | 6.6 [0–16] | -0.7 | -1.7 | 11 |
| Jordan McLaughlin | LIKELY_ACTIVE/ACTIVE | 0.60 | 0.20 | 8.8 | 5.9 [0–15] | -2.9 | -4.1 | 331 |

### TOR vs CHI — 2026-10-21T23:30:00Z — Σ(p·min) JRM 241.5 (raw 244.6), frozen 263.5 raw / 263.5 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Kawhi Leonard | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 30.3 | 30.1 [23–36] | -0.2 | -0.2 | 331 |
| Scottie Barnes | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 31.7 | 30.0 [23–36] | -1.8 | -1.8 | 356 |
| RJ Barrett | LIKELY_ACTIVE/ACTIVE | 0.98 | 1.00 | 30.7 | 29.1 [22–36] | -1.6 | -1.6 | 444 |
| Immanuel Quickley | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 28.5 | 28.3 [21–36] | -0.2 | -0.2 | 394 |
| Jakob Poeltl | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.91 | 24.1 | 22.3 [15–31] | -1.8 | -1.8 | 428 |
| Jamal Shead | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.95 | 20.4 | 20.2 [13–28] | -0.1 | -0.1 | 157 |
| Ja'Kobe Walter | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.97 | 19.6 | 19.1 [11–28] | -0.6 | -0.6 | 124 |
| Kyle Anderson | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.93 | 19.1 | 18.6 [10–27] | -0.5 | -0.5 | 456 |
| Malachi Smith | LIKELY_ACTIVE/ACTIVE | 0.85 | 0.77 | 16.8 | 18.5 [10–27] | +1.7 | +1.7 | 15 |
| Collin Murray-Boyles | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.92 | 18.9 | 17.9 [10–27] | -1.0 | -1.0 | 57 |
| Allen Graves ⚑ | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.62 | 10.8 | 11.4 [4–21] | +0.7 | +0.7 | 0 |
| Jaden Bradley ⚑ | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.55 | 10.7 | 10.6 [4–20] | -0.1 | -0.1 | 0 |
| Jamison Battle | LIKELY_ACTIVE/ACTIVE | 0.65 | 0.32 | 8.2 | 6.2 [0–16] | -1.9 | -1.9 | 119 |
| Trayce Jackson-Davis | LIKELY_ACTIVE/ACTIVE | 0.60 | 0.14 | 7.8 | 6.0 [0–15] | -1.9 | -1.9 | 180 |
| Alijah Martin | LIKELY_ACTIVE/ACTIVE | 0.70 | 0.54 | 7.1 | 5.3 [0–15] | -1.8 | -1.8 | 23 |

### UTA vs MEM — 2026-10-22T00:00:00Z — Σ(p·min) JRM 241.5 (raw 269.4), frozen 265.5 raw / 265.5 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Lauri Markkanen | UNVERIFIED | 0.98 | 0.97 | 32.1 | 29.4 [22–37] | -2.8 | -2.8 | 372 |
| Keyonte George | UNVERIFIED | 0.98 | 0.97 | 29.5 | 28.0 [21–35] | -1.5 | -1.5 | 196 |
| Ace Bailey | UNVERIFIED | 0.97 | 0.98 | 27.9 | 26.5 [19–34] | -1.3 | -1.3 | 72 |
| Jaren Jackson Jr. | UNVERIFIED | 0.95 | 0.86 | 30.4 | 26.4 [19–34] | -4.0 | -4.0 | 397 |
| Kyle Filipowski | UNCERTAIN/QUESTIONABLE | 0.94 | 0.95 | 24.8 | 23.5 [16–31] | -1.3 | -1.3 | 149 |
| Isaiah Collier | UNVERIFIED | 0.79 | 0.88 | 24.4 | 23.2 [16–31] | -1.3 | -1.3 | 130 |
| Brice Sensabaugh | UNVERIFIED | 0.95 | 0.96 | 22.9 | 23.0 [15–31] | +0.0 | +0.0 | 177 |
| Blake Hinson | UNCERTAIN/QUESTIONABLE | 0.80 | 0.86 | 19.2 | 18.2 [10–27] | -1.0 | -1.0 | 14 |
| Jaxson Hayes | UNVERIFIED | 0.91 | 0.86 | 18.2 | 18.1 [10–27] | -0.1 | -0.1 | 434 |
| Josh Okogie | UNVERIFIED | 0.76 | 0.79 | 14.8 | 15.7 [6–25] | +0.9 | +0.9 | 419 |
| Svi Mykhailiuk | UNVERIFIED | 0.46 | 0.33 | 17.3 | 13.5 [4–23] | -3.8 | -3.8 | 336 |
| Tony Bradley | UNVERIFIED | 0.19 | 0.55 | 12.1 | 13.1 [4–22] | +1.0 | +1.0 | 219 |
| Trey Alexander | UNCERTAIN/QUESTIONABLE | 0.25 | 0.47 | 13.4 | 11.9 [5–21] | -1.5 | -1.5 | 32 |
| Josh Green | UNVERIFIED | 0.75 | 0.32 | 13.3 | 11.8 [5–21] | -1.6 | -1.6 | 348 |
| Darryn Peterson ⚑ | UNVERIFIED | 0.58 | 0.64 | 12.5 | 10.7 [4–20] | -1.8 | -1.8 | 0 |
| Mo Bamba | UNVERIFIED | 0.62 | 0.06 | 10.5 | 9.0 [2–19] | -1.4 | -1.4 | 321 |

### WAS vs MIL — 2026-10-21T23:00:00Z — Σ(p·min) JRM 241.5 (raw 262.0), frozen 289.7 raw / 243.6 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Anthony Davis | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 23.6 | 27.5 [20–35] | +3.9 | -0.6 | 342 |
| Bilal Coulibaly | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.97 | 21.3 | 25.4 [18–33] | +4.1 | +0.1 | 178 |
| Will Riley | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 21.1 | 22.9 [15–31] | +1.8 | -2.2 | 74 |
| Deandre Ayton | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.97 | 21.1 | 22.8 [15–31] | +1.7 | -2.3 | 399 |
| Alex Sarr | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.92 | 19.8 | 22.6 [15–31] | +2.7 | -1.0 | 115 |
| Trae Young | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.90 | 20.3 | 22.1 [14–30] | +1.8 | -2.1 | 417 |
| Bub Carrington | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.98 | 19.8 | 21.7 [14–30] | +1.9 | -1.9 | 164 |
| Tre Johnson | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.88 | 18.0 | 20.5 [13–29] | +2.6 | -0.8 | 60 |
| Anthony Gill | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.97 | 17.3 | 18.9 [11–28] | +1.6 | -1.6 | 274 |
| Kyshawn George | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.49 | 20.0 | 18.7 [11–27] | -1.3 | -5.0 | 116 |
| Justin Champagnie | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.83 | 16.6 | 18.1 [10–27] | +1.5 | -1.6 | 185 |
| Khris Middleton | LIKELY_ACTIVE/ACTIVE | 0.57 | 0.70 | 16.1 | 14.6 [6–24] | -1.5 | -4.5 | 384 |
| Felix Okpara ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.61 | 10.5 | 12.2 [3–21] | +1.7 | -0.3 | 0 |
| Reece Beekman | LIKELY_ACTIVE/ACTIVE | 0.82 | 0.36 | 11.5 | 9.6 [3–19] | -2.0 | -4.2 | 35 |
| Tre Mann | LIKELY_ACTIVE/ACTIVE | 0.56 | 0.14 | 8.4 | 6.3 [0–16] | -2.1 | -3.7 | 234 |

⚑ = fewer than 3 career games in the data (role is prior-driven; shown at Low reliability).

## Largest differences, investigated

| player | team | availability | frozen raw → gated | JRM | Δ vs gated | Δ vs raw | p frozen→JRM | note |
|---|---|---|---|---:|---:|---:|---|---|
| Damian Lillard | POR | UNVERIFIED | 29.8 → 29.8 | 18.1 | -11.7 | -11.7 | 0.51→0.59 | depth: more higher-level teammates available; rank-aware heads and conservation reduce him |
| Derrick Jones Jr. | LAC | UNVERIFIED | 24.3 → 33.2 | 26.3 | -6.9 | +2.0 | 0.97→0.98 | the frozen gate scaled him down; JRM keeps his own-history level |
| Ousmane Dieng | MIL | LIKELY_ACTIVE | 19.5 → 15.4 | 22.0 | +6.6 | +2.6 | 0.99→0.98 | set features raise him (thin competition at his position/level in the available set) |
| Jeremiah Fears | NOP | LIKELY_ACTIVE | 23.0 → 16.4 | 22.9 | +6.6 | -0.1 | 0.98→0.99 | the frozen gate scaled him down; JRM keeps his own-history level |
| Saddiq Bey | NOP | LIKELY_ACTIVE | 30.8 → 22.0 | 28.5 | +6.5 | -2.4 | 0.99→0.99 | the frozen gate scaled him down; JRM keeps his own-history level |
| Brook Lopez | LAC | UNVERIFIED | 22.7 → 31.1 | 24.6 | -6.5 | +1.9 | 0.98→0.99 | the frozen gate scaled him down; JRM keeps his own-history level |
| Trey Murphy III | NOP | LIKELY_ACTIVE | 33.9 → 24.1 | 30.6 | +6.4 | -3.3 | 0.98→0.99 | depth: more higher-level teammates available; rank-aware heads and conservation reduce him |
| Kris Dunn | LAC | UNVERIFIED | 22.9 → 31.3 | 25.0 | -6.3 | +2.1 | 0.98→0.99 | the frozen gate scaled him down; JRM keeps his own-history level |
| Hannes Steinbach | CHA | LIKELY_ACTIVE | 12.0 → 12.0 | 18.0 | +6.0 | +6.0 | 0.75→0.68 | no/thin NBA history: role from priors |
| Egor Demin | BKN | LIKELY_ACTIVE | 23.2 → 18.7 | 24.5 | +5.8 | +1.2 | 0.99→0.96 | the frozen gate scaled him down; JRM keeps his own-history level |
| Darius Garland | LAC | UNVERIFIED | 27.9 → 38.2 | 32.4 | -5.8 | +4.5 | 0.96→0.99 | set features raise him (thin competition at his position/level in the available set) |
| Noah Clowney | BKN | LIKELY_ACTIVE | 22.7 → 18.2 | 23.9 | +5.7 | +1.3 | 0.94→0.95 | the frozen gate scaled him down; JRM keeps his own-history level |
| Josh Hart | NYK | UNCERTAIN | 26.9 → 21.8 | 27.3 | +5.6 | +0.5 | 0.96→0.96 | the frozen gate scaled him down; JRM keeps his own-history level |
| Ty Jerome | MEM | UNVERIFIED | 21.2 → 17.8 | 23.3 | +5.6 | +2.2 | 0.93→0.89 | the frozen gate scaled him down; JRM keeps his own-history level |
| Ryan Rollins | MIL | LIKELY_ACTIVE | 30.4 → 24.1 | 29.6 | +5.4 | -0.8 | 0.99→0.99 | the frozen gate scaled him down; JRM keeps his own-history level |

Established rotation (≥ 20 career games, JRM rank ≤ 8, p ≥ 0.5; n = 186): mean conditional minutes frozen raw 26.04, frozen gated 24.00, JRM 25.49.
No/thin-history players (n = 52): JRM 12.87 vs frozen raw 12.22 (JRM higher by +0.65); p JRM 0.62 vs frozen 0.67.

## Remaining structural issues

* Raw (pre-conservation) JRM sums range 212-269; the correction is spread equally per eligible player (largest: LAC +29.8 min over ~13 players).
* Players with no NBA history carry JRM minutes above the frozen prior on average, and BOS' two rookies are the clearest case; their eligibility probability is unobservable from the historical pool (never-dressed roster members are absent from training).
* No injury report yet for most teams (`UNVERIFIED`): JRM's eligibility head is then the history-only head (Brier 0.079 on 2025-26 vs 0.038 with the report), so participation uncertainty is wide until the reports land; snapshots will be re-archived at each report.