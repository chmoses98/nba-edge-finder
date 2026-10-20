# Live-slate audit of the joint rotation model (research shadow)

Feed generated 2026-10-20T22:40:46Z (model pf-1.2.1+f111dea); 26 teams, 13 games, 448 players. JRM = candidate; frozen = the engine currently publishing. Minutes are conditional on playing. 'adj' = the conservation correction JRM applied to its own raw scenario sum.

## Team totals

| team | start (UTC) | roster | Σp frozen | Σp JRM | frozen Σp·m raw | frozen after gate | JRM raw | JRM final | JRM adj (min) | frozen gate scale |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| NOP | 10-22T00:00 | 18 | 15.8 | 11.9 | 340.5 | 243.7 | 277.2 | 241.5 | -35.7 | 0.709 |
| HOU | 10-22T00:30 | 17 | 14.6 | 11.8 | 315.2 | 243.2 | 263.8 | 241.5 | -22.3 | 0.766 |
| MIL | 10-21T23:00 | 17 | 15.0 | 12.2 | 306.6 | 243.3 | 255.8 | 241.5 | -14.3 | 0.788 |
| MEM | 10-22T00:00 | 18 | 15.3 | 12.6 | 305.1 | 243.5 | 270.4 | 241.5 | -28.9 | 0.792 |
| BKN | 10-21T23:30 | 18 | 15.5 | 12.1 | 303.6 | 243.2 | 266.8 | 241.5 | -25.3 | 0.795 |
| NYK | 10-20T23:00 | 17 | 14.7 | 11.3 | 300.2 | 243.3 | 249.1 | 241.5 | -7.6 | 0.804 |
| WAS | 10-21T23:00 | 18 | 13.4 | 11.8 | 290.4 | 243.5 | 271.3 | 241.5 | -29.8 | 0.832 |
| MIN | 10-21T23:30 | 16 | 12.8 | 11.5 | 286.4 | 243.2 | 251.2 | 241.5 | -9.7 | 0.843 |
| ATL | 10-21T23:00 | 18 | 13.0 | 11.2 | 285.1 | 243.1 | 252.0 | 241.5 | -10.5 | 0.847 |
| SAS | 10-21T01:30 | 17 | 13.1 | 11.8 | 276.5 | 243.3 | 260.2 | 241.5 | -18.7 | 0.873 |
| IND | 10-22T00:00 | 17 | 12.2 | 11.0 | 275.6 | 243.2 | 255.3 | 241.5 | -13.8 | 0.876 |
| PHI | 10-20T23:00 | 17 | 11.5 | 11.3 | 273.8 | 243.0 | 255.6 | 241.5 | -14.1 | 0.882 |
| PHX | 10-22T02:00 | 17 | 12.8 | 11.4 | 270.9 | 270.9 | 250.5 | 241.5 | -9.0 | 0.891 |
| MIA | 10-21T23:30 | 17 | 13.8 | 11.9 | 268.8 | 268.8 | 257.9 | 241.5 | -16.4 | 1.000 |
| UTA | 10-22T00:00 | 18 | 12.1 | 11.0 | 266.3 | 266.3 | 258.6 | 241.5 | -17.1 | 1.000 |
| TOR | 10-21T23:30 | 16 | 13.0 | 11.8 | 263.3 | 263.3 | 244.9 | 241.5 | -3.4 | 1.000 |
| LAL | 10-22T02:00 | 18 | 13.3 | 11.4 | 260.4 | 260.4 | 248.9 | 241.5 | -7.4 | 1.000 |
| CHI | 10-21T23:30 | 17 | 12.6 | 11.5 | 256.3 | 256.3 | 254.9 | 241.5 | -13.4 | 1.000 |
| GSW | 10-22T02:00 | 18 | 12.3 | 11.9 | 243.8 | 243.8 | 254.6 | 241.5 | -13.1 | 1.000 |
| ORL | 10-21T23:00 | 17 | 11.2 | 11.0 | 240.1 | 240.1 | 252.0 | 241.5 | -10.5 | 1.000 |
| POR | 10-22T02:00 | 17 | 10.5 | 10.7 | 233.9 | 233.9 | 245.0 | 241.5 | -3.5 | 1.000 |
| DAL | 10-22T00:30 | 17 | 11.0 | 10.9 | 232.7 | 232.7 | 260.1 | 241.5 | -18.6 | 1.000 |
| OKC | 10-21T01:30 | 17 | 11.9 | 11.8 | 231.3 | 231.3 | 259.5 | 241.5 | -18.0 | 1.000 |
| CHA | 10-21T23:30 | 17 | 11.2 | 11.0 | 227.1 | 227.1 | 233.1 | 241.5 | +8.4 | 1.000 |
| SAC | 10-22T02:30 | 16 | 9.7 | 10.4 | 216.0 | 216.0 | 244.6 | 241.5 | -3.1 | 1.000 |
| LAC | 10-22T02:30 | 18 | 9.9 | 11.0 | 176.8 | 242.7 | 236.6 | 241.5 | +4.9 | 1.366 |

Mean: frozen raw 267.2, frozen after gate 245.1, JRM raw 255.0 (|adj| mean 14.5, max 35.7), JRM final 241.5. Historical opener raw SD is 17 min, in-season 5.7 (artifacts/MINUTES_COMPARISON.md); live raw SD 10.1.

## Rotation, minutes and probabilities by team (players with p ≥ 0.05, ordered by JRM conditional minutes)

### ATL vs ORL — 2026-10-21T23:00:00Z — Σ(p·min) JRM 241.5 (raw 252.0), frozen 285.1 raw / 243.1 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Jalen Johnson | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 28.8 | 34.3 [28–40] | +5.6 | +0.6 | 254 |
| Nickeil Alexander-Walker | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 27.8 | 32.7 [27–38] | +4.9 | +0.1 | 459 |
| Dyson Daniels | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 26.6 | 30.8 [24–37] | +4.2 | -0.4 | 271 |
| Onyeka Okongwu | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 25.2 | 29.4 [22–37] | +4.2 | -0.1 | 381 |
| CJ McCollum | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 24.4 | 28.9 [22–36] | +4.6 | +0.4 | 452 |
| Luguentz Dort | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.92 | 20.4 | 20.9 [13–29] | +0.6 | -3.0 | 433 |
| Jock Landale | LIKELY_ACTIVE/ACTIVE | 0.89 | 0.92 | 17.0 | 18.2 [10–27] | +1.2 | -1.8 | 288 |
| Aaron Wiggins | LIKELY_ACTIVE/ACTIVE | 0.88 | 0.83 | 14.9 | 13.4 [4–23] | -1.4 | -4.0 | 339 |
| Corey Kispert | LIKELY_ACTIVE/ACTIVE | 0.90 | 0.81 | 13.2 | 12.3 [3–21] | -0.9 | -3.2 | 350 |
| Jalen Wilson | UNCERTAIN/QUESTIONABLE | 0.74 | 0.88 | 14.3 | 12.2 [3–21] | -2.1 | -4.5 | 175 |
| Keshon Gilbert | UNCERTAIN/QUESTIONABLE | 0.70 | 0.55 | 12.8 | 11.8 [5–21] | -0.9 | -3.1 | 4 |
| Dorian Finney-Smith | LIKELY_ACTIVE/ACTIVE | 0.77 | 0.34 | 13.0 | 11.4 [4–21] | -1.6 | -3.9 | 445 |
| Asa Newell | LIKELY_ACTIVE/ACTIVE | 0.62 | 0.52 | 11.3 | 8.6 [2–18] | -2.7 | -4.7 | 43 |
| Zuby Ejiofor ⚑ | LIKELY_ACTIVE/ACTIVE | 0.66 | 0.32 | 9.9 | 7.9 [1–17] | -2.0 | -3.7 | 0 |
| Kingston Flemings ⚑ | LIKELY_ACTIVE/ACTIVE | 0.66 | 0.17 | 10.0 | 7.5 [1–17] | -2.5 | -4.2 | 0 |

### BKN vs CHA — 2026-10-21T23:30:00Z — Σ(p·min) JRM 241.5 (raw 266.8), frozen 303.6 raw / 243.2 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Michael Porter Jr. | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 25.6 | 32.2 [25–39] | +6.6 | +0.3 | 397 |
| Julius Randle | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 25.1 | 30.2 [23–37] | +5.1 | -1.2 | 478 |
| Noah Clowney | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.98 | 18.2 | 23.6 [16–31] | +5.5 | +1.0 | 135 |
| Egor Demin | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.97 | 18.6 | 22.7 [15–31] | +4.0 | -0.6 | 52 |
| Terance Mann | LIKELY_ACTIVE/ACTIVE | 0.93 | 0.93 | 17.4 | 19.7 [12–28] | +2.3 | -2.0 | 464 |
| Day'Ron Sharpe | LIKELY_ACTIVE/ACTIVE | 0.89 | 0.88 | 15.5 | 18.3 [10–27] | +2.9 | -1.0 | 252 |
| Danny Wolf | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.89 | 15.7 | 18.2 [10–27] | +2.5 | -1.3 | 57 |
| Nolan Traore | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.85 | 15.5 | 17.7 [10–26] | +2.2 | -1.6 | 56 |
| Josh Minott | LIKELY_ACTIVE/ACTIVE | 0.89 | 0.87 | 14.5 | 17.0 [9–26] | +2.5 | -1.1 | 139 |
| Keon Ellis | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.85 | 15.1 | 16.5 [8–25] | +1.4 | -2.3 | 224 |
| Drake Powell | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.88 | 15.9 | 16.4 [8–25] | +0.5 | -3.5 | 63 |
| Ben Saraf | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.79 | 14.5 | 14.8 [6–24] | +0.2 | -3.4 | 44 |
| Joshua Jefferson ⚑ | LIKELY_ACTIVE/ACTIVE | 0.76 | 0.45 | 11.2 | 12.5 [3–22] | +1.3 | -1.5 | 0 |
| Mikel Brown Jr. ⚑ | LIKELY_ACTIVE/ACTIVE | 0.76 | 0.27 | 11.3 | 12.2 [3–21] | +1.0 | -1.8 | 0 |
| Chaney Johnson | LIKELY_ACTIVE/ACTIVE | 0.88 | 0.48 | 11.2 | 9.8 [3–19] | -1.4 | -4.2 | 17 |

### CHA vs BKN — 2026-10-21T23:30:00Z — Σ(p·min) JRM 241.5 (raw 233.1), frozen 227.1 raw / 227.1 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Brandon Miller | LIKELY_ACTIVE/ACTIVE | 0.99 | 1.00 | 29.8 | 33.2 [27–39] | +3.4 | +3.4 | 166 |
| Grayson Allen | UNCERTAIN/QUESTIONABLE | 0.88 | 0.97 | 23.9 | 26.7 [19–34] | +2.8 | +2.8 | 416 |
| Naz Reid | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.97 | 23.4 | 26.0 [19–34] | +2.6 | +2.6 | 483 |
| Moussa Diabate | UNCERTAIN/QUESTIONABLE | 0.96 | 0.98 | 23.7 | 25.8 [19–33] | +2.1 | +2.1 | 176 |
| Dennis Schroder | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.89 | 21.1 | 22.4 [15–31] | +1.3 | +1.3 | 481 |
| Royce O'Neale | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.96 | 23.5 | 22.0 [14–30] | -1.5 | -1.5 | 527 |
| Sion James | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.89 | 22.2 | 20.8 [13–29] | -1.4 | -1.4 | 82 |
| Ryan Kalkbrenner | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.92 | 20.8 | 19.2 [11–28] | -1.5 | -1.5 | 69 |
| Tidjane Salaun | LIKELY_ACTIVE/ACTIVE | 0.62 | 0.76 | 14.6 | 17.3 [9–26] | +2.7 | +2.7 | 97 |
| Hannes Steinbach ⚑ | LIKELY_ACTIVE/ACTIVE | 0.76 | 0.67 | 12.0 | 16.2 [7–25] | +4.2 | +4.2 | 0 |
| Christian Anderson ⚑ | LIKELY_ACTIVE/ACTIVE | 0.76 | 0.70 | 13.4 | 15.6 [6–25] | +2.2 | +2.2 | 0 |
| PJ Hall | LIKELY_ACTIVE/ACTIVE | 0.86 | 0.80 | 13.1 | 15.6 [6–25] | +2.5 | +2.5 | 36 |
| Liam McNeeley | LIKELY_ACTIVE/ACTIVE | 0.56 | 0.49 | 14.4 | 14.4 [5–23] | -0.1 | -0.1 | 31 |

### CHI vs TOR — 2026-10-21T23:30:00Z — Σ(p·min) JRM 241.5 (raw 254.9), frozen 256.3 raw / 256.3 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Josh Giddey | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.99 | 29.6 | 31.1 [24–37] | +1.5 | +1.5 | 334 |
| Matas Buzelis | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 30.1 | 30.8 [24–37] | +0.7 | +0.7 | 157 |
| Norman Powell | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.98 | 24.6 | 26.5 [19–34] | +1.9 | +1.9 | 420 |
| Isaac Okoro | LIKELY_ACTIVE/PROBABLE | 0.99 | 0.99 | 25.9 | 25.8 [19–34] | -0.1 | -0.1 | 397 |
| Tre Jones | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.99 | 25.8 | 25.5 [18–33] | -0.2 | -0.2 | 362 |
| Jalen Smith | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.94 | 21.1 | 21.9 [14–30] | +0.8 | +0.8 | 323 |
| Leonard Miller | LIKELY_ACTIVE/PROBABLE | 0.99 | 0.87 | 19.2 | 16.4 [8–25] | -2.8 | -2.8 | 76 |
| Zach Collins | LIKELY_ACTIVE/PROBABLE | 0.93 | 0.73 | 16.5 | 16.2 [7–25] | -0.3 | -0.3 | 245 |
| Patrick Williams | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.91 | 19.5 | 16.1 [7–25] | -3.4 | -3.4 | 348 |
| Tobe Awaka ⚑ | LIKELY_ACTIVE/PROBABLE | 0.92 | 0.72 | 14.3 | 14.5 [5–24] | +0.2 | +0.2 | 0 |
| Caleb Wilson ⚑ | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.72 | 14.3 | 14.3 [5–23] | -0.0 | -0.0 | 0 |
| Jaylin Sellers ⚑ | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.71 | 14.0 | 14.0 [5–23] | +0.0 | +0.0 | 0 |
| Buddy Hield | LIKELY_ACTIVE/ACTIVE | 0.73 | 0.59 | 13.4 | 13.4 [4–23] | +0.0 | +0.0 | 522 |
| Noa Essengue ⚑ | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.36 | 8.5 | 8.2 [1–18] | -0.3 | -0.3 | 2 |

### DAL vs HOU — 2026-10-22T00:30:00Z — Σ(p·min) JRM 241.5 (raw 260.1), frozen 232.7 raw / 232.7 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Kyrie Irving | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.98 | 32.2 | 35.3 [29–41] | +3.1 | +3.1 | 271 |
| Cooper Flagg | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.96 | 30.7 | 33.0 [27–38] | +2.2 | +2.2 | 70 |
| Naji Marshall | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.98 | 28.4 | 30.4 [24–37] | +2.0 | +2.0 | 371 |
| P.J. Washington | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.99 | 28.7 | 29.0 [22–36] | +0.3 | +0.3 | 446 |
| Max Christie | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.99 | 26.6 | 25.5 [18–33] | -1.0 | -1.0 | 262 |
| Daniel Gafford | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.94 | 20.3 | 21.1 [13–29] | +0.8 | +0.8 | 433 |
| Zaccharie Risacher | LIKELY_ACTIVE/ACTIVE | 0.85 | 0.79 | 17.7 | 16.6 [8–25] | -1.1 | -1.1 | 142 |
| Jett Howard | UNCERTAIN/QUESTIONABLE | 0.64 | 0.78 | 13.6 | 15.0 [6–24] | +1.4 | +1.4 | 133 |
| Sergio de Larrea ⚑ | LIKELY_ACTIVE/ACTIVE | 0.76 | 0.71 | 14.1 | 14.3 [5–23] | +0.1 | +0.1 | 0 |
| Tobi Lawal ⚑ | LIKELY_ACTIVE/ACTIVE | 0.76 | 0.69 | 14.1 | 14.1 [5–23] | -0.0 | -0.0 | 0 |
| Morez Johnson Jr. ⚑ | LIKELY_ACTIVE/ACTIVE | 0.76 | 0.65 | 14.1 | 13.6 [4–23] | -0.6 | -0.6 | 0 |
| Marcus Sasser | LIKELY_ACTIVE/ACTIVE | 0.77 | 0.68 | 11.5 | 13.0 [4–22] | +1.5 | +1.5 | 166 |
| Moussa Cisse | LIKELY_ACTIVE/ACTIVE | 0.88 | 0.75 | 16.1 | 11.7 [5–21] | -4.4 | -4.4 | 37 |

### GSW vs LAL — 2026-10-22T02:00:00Z — Σ(p·min) JRM 241.5 (raw 254.6), frozen 243.8 raw / 243.8 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Stephen Curry | UNCERTAIN/QUESTIONABLE | 0.94 | 0.98 | 29.8 | 30.8 [24–37] | +0.9 | +0.9 | 375 |
| Brandin Podziemski | UNCERTAIN/QUESTIONABLE | 0.97 | 0.98 | 28.1 | 28.3 [21–36] | +0.3 | +0.3 | 219 |
| Draymond Green | UNVERIFIED | 0.94 | 0.97 | 24.8 | 24.2 [17–32] | -0.6 | -0.6 | 415 |
| Brandon Williams | UNVERIFIED | 0.94 | 0.95 | 20.5 | 22.8 [15–31] | +2.3 | +2.3 | 139 |
| Gui Santos | UNVERIFIED | 0.96 | 0.97 | 22.0 | 22.6 [15–31] | +0.6 | +0.6 | 147 |
| De'Anthony Melton | UNVERIFIED | 0.94 | 0.96 | 22.2 | 21.0 [13–29] | -1.1 | -1.1 | 355 |
| Al Horford | UNVERIFIED | 0.90 | 0.94 | 22.2 | 20.5 [13–29] | -1.8 | -1.8 | 397 |
| Gary Payton II | UNVERIFIED | 0.81 | 0.87 | 16.9 | 17.9 [10–27] | +1.0 | +1.0 | 305 |
| Georges Niang | UNVERIFIED | 0.65 | 0.62 | 16.3 | 16.8 [9–26] | +0.4 | +0.4 | 453 |
| Will Richard | UNVERIFIED | 0.82 | 0.75 | 16.6 | 16.4 [8–25] | -0.2 | -0.2 | 69 |
| LJ Cryer | UNVERIFIED | 0.78 | 0.85 | 15.4 | 16.0 [7–25] | +0.6 | +0.6 | 18 |
| Graham Ike ⚑ | UNVERIFIED | 0.59 | 0.69 | 12.9 | 13.0 [4–22] | +0.1 | +0.1 | 0 |
| Yaxel Lendeborg ⚑ | UNVERIFIED | 0.59 | 0.42 | 12.9 | 12.6 [4–22] | -0.4 | -0.4 | 0 |
| Charles Bassey | UNCERTAIN/QUESTIONABLE | 0.72 | 0.76 | 13.1 | 11.3 [4–21] | -1.8 | -1.8 | 124 |
| Malevy Leons | UNVERIFIED | 0.80 | 0.18 | 11.8 | 7.9 [1–17] | -3.9 | -3.9 | 31 |

### HOU vs DAL — 2026-10-22T00:30:00Z — Σ(p·min) JRM 241.5 (raw 263.8), frozen 315.2 raw / 243.2 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Kevin Durant | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 26.8 | 31.7 [25–38] | +4.9 | -3.0 | 352 |
| Amen Thompson | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 26.2 | 30.5 [24–37] | +4.3 | -3.5 | 210 |
| Jabari Smith Jr. | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 25.6 | 30.1 [23–36] | +4.6 | -3.0 | 289 |
| Alperen Sengun | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 25.0 | 30.0 [23–36] | +5.0 | -2.4 | 358 |
| Fred VanVleet | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.99 | 22.5 | 27.2 [20–34] | +4.7 | -2.0 | 373 |
| Reed Sheppard | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 17.6 | 20.8 [13–29] | +3.2 | -2.1 | 134 |
| Marcus Smart | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.97 | 18.9 | 20.2 [13–28] | +1.4 | -4.2 | 356 |
| Tari Eason | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.96 | 16.9 | 19.6 [11–28] | +2.8 | -2.2 | 221 |
| Steven Adams | UNCERTAIN/QUESTIONABLE | 0.84 | 0.83 | 15.1 | 15.0 [6–24] | -0.1 | -4.6 | 327 |
| Bogdan Bogdanovic | LIKELY_ACTIVE/ACTIVE | 0.72 | 0.49 | 11.3 | 10.1 [3–20] | -1.2 | -4.6 | 378 |
| Oscar Tshiebwe | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.76 | 10.8 | 8.3 [1–18] | -2.4 | -5.6 | 50 |
| Clint Capela | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.66 | 9.9 | 6.3 [0–16] | -3.6 | -6.5 | 444 |
| Julian Phillips | UNCERTAIN/QUESTIONABLE | 0.45 | 0.54 | 8.2 | 5.7 [0–15] | -2.5 | -5.0 | 166 |
| Quadir Copeland ⚑ | LIKELY_ACTIVE/ACTIVE | 0.76 | 0.20 | 8.6 | 5.1 [0–15] | -3.5 | -6.0 | 0 |
| Jae'Sean Tate | LIKELY_ACTIVE/ACTIVE | 0.91 | 0.36 | 9.0 | 4.9 [0–14] | -4.2 | -6.8 | 341 |

### IND vs NOP — 2026-10-22T00:00:00Z — Σ(p·min) JRM 241.5 (raw 255.3), frozen 275.6 raw / 243.2 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Pascal Siakam | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.99 | 27.7 | 32.0 [25–38] | +4.3 | +0.6 | 475 |
| Andrew Nembhard | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.99 | 26.1 | 30.4 [24–37] | +4.3 | +0.8 | 264 |
| Tyrese Haliburton | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.98 | 24.6 | 30.3 [24–37] | +5.7 | +2.5 | 334 |
| Ivica Zubac | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.98 | 22.3 | 26.2 [19–34] | +3.8 | +0.9 | 491 |
| Kelly Oubre Jr. | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.97 | 23.2 | 25.6 [18–33] | +2.3 | -0.8 | 413 |
| Jarace Walker | UNCERTAIN/QUESTIONABLE | 0.93 | 0.96 | 21.5 | 24.2 [17–32] | +2.8 | -0.1 | 184 |
| Jay Huff | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.91 | 17.6 | 18.1 [10–27] | +0.5 | -1.8 | 176 |
| Obi Toppin | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.86 | 16.2 | 15.9 [7–25] | -0.3 | -2.5 | 387 |
| Kobe Brown | LIKELY_ACTIVE/PROBABLE | 0.99 | 0.87 | 17.3 | 15.5 [6–25] | -1.8 | -4.2 | 141 |
| Quenton Jackson | LIKELY_ACTIVE/ACTIVE | 0.93 | 0.71 | 16.9 | 14.4 [5–23] | -2.5 | -4.7 | 89 |
| Ben Sheppard | LIKELY_ACTIVE/ACTIVE | 0.87 | 0.66 | 16.4 | 14.4 [5–23] | -2.0 | -4.1 | 185 |
| Jalen Slawson | LIKELY_ACTIVE/PROBABLE | 0.97 | 0.73 | 14.2 | 11.3 [4–21] | -2.8 | -4.7 | 24 |
| Larry Nance Jr. | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.41 | 12.6 | 10.8 [4–20] | -1.8 | -3.5 | 322 |

### LAC vs SAC — 2026-10-22T02:30:00Z — Σ(p·min) JRM 241.5 (raw 236.6), frozen 176.8 raw / 242.7 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Darius Garland | UNVERIFIED | 0.96 | 0.99 | 38.3 | 30.8 [24–37] | -7.5 | +2.9 | 427 |
| Kris Dunn | UNVERIFIED | 0.98 | 0.99 | 31.4 | 25.8 [19–33] | -5.6 | +3.0 | 311 |
| Derrick Jones Jr. | UNVERIFIED | 0.96 | 0.98 | 33.3 | 25.7 [18–33] | -7.6 | +1.4 | 433 |
| Brook Lopez | UNVERIFIED | 0.98 | 0.99 | 31.1 | 25.6 [18–33] | -5.5 | +3.0 | 464 |
| Rui Hachimura | UNVERIFIED | 0.91 | 0.98 | 31.9 | 25.4 [18–33] | -6.5 | +2.1 | 406 |
| Kobe Sanders | UNVERIFIED | 0.81 | 0.91 | 22.8 | 21.3 [14–29] | -1.6 | +4.6 | 68 |
| Isaiah Jackson | UNVERIFIED | 0.60 | 0.88 | 20.9 | 21.2 [14–29] | +0.4 | +6.0 | 217 |
| Jalen Pickett | UNVERIFIED | 0.58 | 0.79 | 20.4 | 20.9 [13–29] | +0.5 | +6.0 | 124 |
| Gradey Dick | UNVERIFIED | 0.58 | 0.74 | 13.6 | 17.6 [10–26] | +4.0 | +7.7 | 190 |
| Keaton Wagler ⚑ | UNVERIFIED | 0.63 | 0.69 | 14.6 | 16.3 [7–25] | +1.7 | +5.6 | 0 |
| Nick Martinelli ⚑ | UNVERIFIED | 0.63 | 0.73 | 14.4 | 16.0 [7–25] | +1.6 | +5.5 | 0 |
| Baba Miller ⚑ | UNVERIFIED | 0.63 | 0.73 | 14.4 | 15.6 [6–25] | +1.2 | +5.1 | 0 |
| Cam Christie | UNVERIFIED | 0.63 | 0.62 | 9.4 | 12.2 [5–22] | +2.7 | +5.3 | 66 |

### LAL vs GSW — 2026-10-22T02:00:00Z — Σ(p·min) JRM 241.5 (raw 248.9), frozen 260.4 raw / 260.4 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Luka Doncic | UNVERIFIED | 0.96 | 0.96 | 34.1 | 35.6 [29–41] | +1.5 | +1.5 | 442 |
| Austin Reaves | UNVERIFIED | 0.95 | 0.96 | 32.4 | 34.9 [29–40] | +2.5 | +2.5 | 332 |
| Walker Kessler | UNVERIFIED | 0.90 | 0.96 | 26.4 | 28.0 [21–35] | +1.6 | +1.6 | 201 |
| Quentin Grimes | UNVERIFIED | 0.90 | 0.97 | 22.1 | 22.7 [15–31] | +0.6 | +0.6 | 314 |
| Collin Sexton | UNCERTAIN/QUESTIONABLE | 0.84 | 0.96 | 22.5 | 21.9 [14–30] | -0.6 | -0.6 | 393 |
| Ziaire Williams | UNVERIFIED | 0.93 | 0.92 | 20.0 | 21.6 [14–30] | +1.6 | +1.6 | 267 |
| Sandro Mamukelashvili | UNVERIFIED | 0.89 | 0.90 | 21.1 | 20.2 [13–28] | -0.9 | -0.9 | 268 |
| Jake LaRavia | UNVERIFIED | 0.97 | 0.97 | 22.6 | 19.8 [12–28] | -2.8 | -2.8 | 218 |
| Jaden Hardy | UNVERIFIED | 0.78 | 0.81 | 17.8 | 16.6 [8–25] | -1.2 | -1.2 | 234 |
| Matisse Thybulle | UNVERIFIED | 0.60 | 0.69 | 17.0 | 15.6 [6–25] | -1.4 | -1.4 | 374 |
| Jarred Vanderbilt | UNCERTAIN/QUESTIONABLE | 0.75 | 0.67 | 13.7 | 12.2 [5–22] | -1.6 | -1.6 | 358 |
| Kevon Looney | UNVERIFIED | 0.68 | 0.30 | 11.9 | 9.5 [2–19] | -2.4 | -2.4 | 416 |
| Arthur Kaluma ⚑ | UNVERIFIED | 0.59 | 0.38 | 10.8 | 8.9 [2–18] | -1.9 | -1.9 | 0 |
| Cameron Carr ⚑ | UNCERTAIN/QUESTIONABLE | 0.49 | 0.21 | 10.9 | 8.6 [2–18] | -2.3 | -2.3 | 0 |
| Bronny James | UNCERTAIN/QUESTIONABLE | 0.69 | 0.68 | 12.0 | 8.5 [1–18] | -3.5 | -3.5 | 68 |

### MEM vs UTA — 2026-10-22T00:00:00Z — Σ(p·min) JRM 241.5 (raw 270.4), frozen 305.1 raw / 243.5 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Jerami Grant | UNCERTAIN/QUESTIONABLE | 0.96 | 0.97 | 22.4 | 26.7 [19–34] | +4.3 | -1.4 | 393 |
| GG Jackson | UNCERTAIN/QUESTIONABLE | 0.85 | 0.92 | 17.7 | 21.7 [14–30] | +4.0 | -0.5 | 131 |
| Jaylen Wells | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.98 | 19.8 | 21.5 [14–30] | +1.7 | -3.4 | 148 |
| Ty Jerome | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.95 | 16.8 | 21.5 [14–30] | +4.7 | +0.4 | 244 |
| Zach Edey | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.97 | 17.0 | 20.5 [13–29] | +3.5 | -0.8 | 77 |
| Cedric Coward | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.95 | 18.6 | 20.0 [12–28] | +1.4 | -3.3 | 62 |
| Scotty Pippen Jr. | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.93 | 16.6 | 19.4 [11–28] | +2.8 | -1.4 | 116 |
| Taylor Hendricks | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.94 | 17.3 | 19.2 [11–28] | +1.9 | -2.5 | 102 |
| Javon Small | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.86 | 14.6 | 18.5 [10–27] | +3.9 | +0.2 | 40 |
| Olivier-Maxence Prosper | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.84 | 17.4 | 18.3 [10–27] | +0.9 | -3.5 | 142 |
| Cam Spencer | LIKELY_ACTIVE/ACTIVE | 0.91 | 0.83 | 16.8 | 17.6 [9–26] | +0.8 | -3.4 | 97 |
| Kris Murray | LIKELY_ACTIVE/ACTIVE | 0.87 | 0.81 | 15.6 | 16.1 [7–25] | +0.5 | -3.4 | 188 |
| Jahmai Mashack | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.90 | 15.4 | 13.9 [5–23] | -1.5 | -5.4 | 30 |
| Quinten Post | LIKELY_ACTIVE/ACTIVE | 0.90 | 0.47 | 11.1 | 11.2 [4–21] | +0.2 | -2.6 | 109 |
| Cameron Boozer ⚑ | LIKELY_ACTIVE/ACTIVE | 0.72 | 0.19 | 9.3 | 8.0 [1–17] | -1.3 | -3.7 | 0 |

### MIA vs MIN — 2026-10-21T23:30:00Z — Σ(p·min) JRM 241.5 (raw 257.9), frozen 268.8 raw / 268.8 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Bam Adebayo | UNCERTAIN/QUESTIONABLE | 0.97 | 0.98 | 32.4 | 31.5 [25–38] | -0.9 | -0.9 | 489 |
| Giannis Antetokounmpo | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 27.4 | 27.6 [20–35] | +0.3 | +0.3 | 431 |
| Andrew Wiggins | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 27.9 | 26.4 [19–34] | -1.4 | -1.4 | 434 |
| Davion Mitchell | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 25.6 | 24.6 [17–32] | -0.9 | -0.9 | 370 |
| Pelle Larsson | UNCERTAIN/QUESTIONABLE | 0.93 | 0.97 | 23.5 | 23.7 [16–31] | +0.3 | +0.3 | 124 |
| Bobby Portis | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.96 | 22.4 | 22.3 [15–31] | -0.0 | -0.0 | 473 |
| Klay Thompson | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.92 | 19.0 | 20.4 [13–29] | +1.5 | +1.5 | 319 |
| Tim Hardaway Jr. | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.97 | 22.1 | 19.7 [12–28] | -2.4 | -2.4 | 490 |
| Nick Richards | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.84 | 17.8 | 15.1 [6–24] | -2.7 | -2.7 | 303 |
| Simone Fontecchio | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.83 | 15.0 | 13.6 [5–23] | -1.4 | -1.4 | 262 |
| Nikola Jovic | LIKELY_ACTIVE/ACTIVE | 0.67 | 0.69 | 12.3 | 12.6 [4–22] | +0.2 | +0.2 | 152 |
| Dru Smith | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.68 | 10.8 | 11.4 [4–21] | +0.6 | +0.6 | 108 |
| Tre Donaldson ⚑ | LIKELY_ACTIVE/ACTIVE | 0.66 | 0.35 | 11.7 | 9.5 [2–19] | -2.2 | -2.2 | 0 |
| Ryan Conwell ⚑ | LIKELY_ACTIVE/ACTIVE | 0.66 | 0.18 | 11.7 | 9.2 [2–19] | -2.5 | -2.5 | 0 |
| Keshad Johnson | LIKELY_ACTIVE/ACTIVE | 0.69 | 0.59 | 11.0 | 8.5 [1–18] | -2.5 | -2.5 | 48 |

### MIL vs WAS — 2026-10-21T23:00:00Z — Σ(p·min) JRM 241.5 (raw 255.8), frozen 306.6 raw / 243.3 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Ryan Rollins | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 24.1 | 30.7 [24–37] | +6.6 | +0.3 | 154 |
| Tyler Herro | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.99 | 23.5 | 29.5 [22–37] | +6.1 | -0.0 | 394 |
| Jaime Jaquez Jr. | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.97 | 19.4 | 23.6 [16–31] | +4.2 | -0.9 | 216 |
| Myles Turner | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.98 | 19.8 | 22.8 [15–31] | +3.0 | -2.2 | 434 |
| AJ Green | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 20.0 | 22.1 [14–30] | +2.0 | -3.2 | 240 |
| Kyle Kuzma | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.98 | 18.6 | 22.1 [14–30] | +3.5 | -1.3 | 463 |
| Gary Trent Jr. | LIKELY_ACTIVE/ACTIVE | 0.91 | 0.89 | 14.9 | 17.4 [9–26] | +2.6 | -1.3 | 466 |
| Jericho Sims | UNCERTAIN/QUESTIONABLE | 0.95 | 0.93 | 15.1 | 16.7 [9–25] | +1.6 | -2.3 | 254 |
| Kel'el Ware | LIKELY_ACTIVE/ACTIVE | 0.88 | 0.89 | 15.0 | 16.3 [8–25] | +1.3 | -2.6 | 141 |
| Cormac Ryan | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.78 | 15.9 | 15.0 [6–24] | -0.8 | -5.0 | 11 |
| Caris LeVert | LIKELY_ACTIVE/ACTIVE | 0.80 | 0.71 | 14.2 | 14.1 [5–23] | -0.1 | -3.8 | 416 |
| Ousmane Dieng | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.97 | 15.4 | 13.7 [5–23] | -1.7 | -5.7 | 166 |
| Kasparas Jakucionis | LIKELY_ACTIVE/ACTIVE | 0.75 | 0.62 | 12.6 | 12.6 [4–22] | +0.0 | -3.3 | 53 |
| Kam Jones | LIKELY_ACTIVE/ACTIVE | 0.73 | 0.33 | 11.3 | 9.9 [3–19] | -1.4 | -4.4 | 37 |
| Brayden Burries ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.16 | 9.4 | 8.3 [1–18] | -1.2 | -3.6 | 0 |

### MIN vs MIA — 2026-10-21T23:30:00Z — Σ(p·min) JRM 241.5 (raw 251.2), frozen 286.4 raw / 243.2 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Anthony Edwards | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 27.4 | 34.4 [28–40] | +7.0 | +2.1 | 442 |
| Jaden McDaniels | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 26.8 | 30.8 [24–37] | +4.1 | -0.7 | 439 |
| Rudy Gobert | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 25.6 | 29.4 [22–37] | +3.7 | -0.8 | 499 |
| LaMelo Ball | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 22.7 | 26.9 [20–34] | +4.2 | +0.1 | 303 |
| Ayo Dosunmu | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 22.4 | 26.6 [19–34] | +4.2 | +0.2 | 348 |
| Cody Williams | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.95 | 22.6 | 21.5 [14–30] | -1.1 | -5.1 | 117 |
| Jonathan Kuminga | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.92 | 18.9 | 20.2 [13–28] | +1.3 | -2.0 | 293 |
| Bones Hyland | LIKELY_ACTIVE/ACTIVE | 0.93 | 0.88 | 17.2 | 16.9 [9–26] | -0.4 | -3.4 | 255 |
| Trey Lyles | LIKELY_ACTIVE/ACTIVE | 0.91 | 0.80 | 16.9 | 16.6 [8–25] | -0.4 | -3.4 | 362 |
| Jaylen Clark | LIKELY_ACTIVE/ACTIVE | 0.89 | 0.77 | 13.3 | 9.8 [3–19] | -3.6 | -6.0 | 108 |
| Terrence Shannon Jr. | LIKELY_ACTIVE/ACTIVE | 0.88 | 0.74 | 13.8 | 9.5 [3–19] | -4.3 | -6.7 | 75 |
| Isaiah Evans ⚑ | LIKELY_ACTIVE/ACTIVE | 0.66 | 0.50 | 10.7 | 9.4 [2–19] | -1.3 | -3.1 | 0 |
| Joan Beringer | LIKELY_ACTIVE/ACTIVE | 0.84 | 0.70 | 12.5 | 9.1 [2–19] | -3.4 | -5.7 | 40 |
| Rocco Zikarsky | UNCERTAIN/QUESTIONABLE | 0.34 | 0.22 | 9.0 | 6.9 [0–16] | -2.1 | -3.7 | 5 |
| Zyon Pullin | LIKELY_ACTIVE/ACTIVE | 0.48 | 0.09 | 9.8 | 6.7 [0–16] | -3.1 | -4.8 | 8 |

### NOP vs IND — 2026-10-22T00:00:00Z — Σ(p·min) JRM 241.5 (raw 277.2), frozen 340.5 raw / 243.7 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Trey Murphy III | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.99 | 24.3 | 30.9 [24–37] | +6.6 | -3.0 | 317 |
| Zion Williamson | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 21.8 | 28.8 [22–36] | +7.0 | -1.7 | 276 |
| Saddiq Bey | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 22.1 | 28.5 [21–36] | +6.5 | -2.3 | 364 |
| Dejounte Murray | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.99 | 20.2 | 27.4 [20–35] | +7.3 | -0.7 | 398 |
| Herbert Jones | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.98 | 18.9 | 25.8 [19–34] | +6.9 | -0.6 | 296 |
| Bennedict Mathurin | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.97 | 16.8 | 21.4 [14–30] | +4.6 | -2.0 | 264 |
| Julian Reese | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.93 | 16.7 | 17.8 [10–27] | +1.2 | -5.4 | 13 |
| Bryce McGowens | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.82 | 14.3 | 15.3 [6–24] | +1.0 | -4.7 | 159 |
| Derik Queen | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.94 | 15.0 | 13.8 [5–23] | -1.2 | -7.2 | 81 |
| Jeremiah Fears | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.98 | 16.6 | 13.4 [4–23] | -3.1 | -9.7 | 82 |
| Yves Missi | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.83 | 13.4 | 13.1 [4–22] | -0.2 | -5.5 | 139 |
| Karlo Matkovic | LIKELY_ACTIVE/ACTIVE | 0.87 | 0.77 | 11.3 | 12.0 [5–21] | +0.7 | -3.8 | 104 |
| Jordan Poole | LIKELY_ACTIVE/ACTIVE | 0.90 | 0.46 | 14.8 | 9.1 [2–19] | -5.6 | -11.5 | 451 |
| DeAndre Jordan | LIKELY_ACTIVE/ACTIVE | 0.46 | 0.07 | 9.3 | 6.0 [0–16] | -3.3 | -7.0 | 304 |
| AJ Johnson | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.16 | 8.3 | 5.8 [0–15] | -2.5 | -5.8 | 77 |

### NYK vs PHI — 2026-10-20T23:00:00Z — Σ(p·min) JRM 241.5 (raw 249.1), frozen 300.2 raw / 243.3 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Jalen Brunson | LIKELY_ACTIVE/ACTIVE | 0.98 | 1.00 | 28.4 | 34.4 [28–40] | +6.0 | -0.6 | 488 |
| OG Anunoby | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 27.7 | 34.3 [28–40] | +6.6 | +0.1 | 419 |
| Karl-Anthony Towns | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 25.4 | 31.3 [25–38] | +5.9 | -0.1 | 398 |
| Mikal Bridges | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 23.7 | 27.2 [20–34] | +3.5 | -2.1 | 554 |
| Josh Hart | UNCERTAIN/QUESTIONABLE | 0.96 | 0.96 | 21.8 | 26.7 [19–34] | +4.9 | -0.2 | 467 |
| Miles McBride | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.97 | 18.9 | 21.4 [14–30] | +2.5 | -1.9 | 271 |
| Landry Shamet | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.94 | 17.9 | 21.1 [13–29] | +3.2 | -1.0 | 370 |
| Andre Drummond | LIKELY_ACTIVE/ACTIVE | 0.88 | 0.81 | 14.8 | 14.4 [5–24] | -0.3 | -3.8 | 425 |
| Jordan Clarkson | LIKELY_ACTIVE/ACTIVE | 0.93 | 0.76 | 12.5 | 13.3 [4–22] | +0.8 | -2.1 | 444 |
| Jose Alvarado | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.71 | 14.6 | 12.2 [3–21] | -2.4 | -5.8 | 296 |
| James Wiseman | LIKELY_ACTIVE/ACTIVE | 0.83 | 0.65 | 11.4 | 12.0 [5–21] | +0.6 | -2.1 | 152 |
| Mohamed Diawara | LIKELY_ACTIVE/ACTIVE | 0.84 | 0.55 | 9.9 | 7.5 [1–17] | -2.4 | -4.7 | 68 |
| Jaden Akins ⚑ | LIKELY_ACTIVE/ACTIVE | 0.77 | 0.56 | 8.6 | 7.0 [0–16] | -1.7 | -3.7 | 0 |
| Tyler Nickel ⚑ | LIKELY_ACTIVE/ACTIVE | 0.77 | 0.34 | 8.7 | 6.7 [0–16] | -1.9 | -3.9 | 0 |
| Pacome Dadiet | LIKELY_ACTIVE/ACTIVE | 0.59 | 0.10 | 7.3 | 5.2 [0–15] | -2.1 | -3.9 | 46 |

### OKC vs SAS — 2026-10-21T01:30:00Z — Σ(p·min) JRM 241.5 (raw 259.5), frozen 231.3 raw / 231.3 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Shai Gilgeous-Alexander | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 33.6 | 34.0 [28–39] | +0.5 | +0.5 | 449 |
| Jalen Williams | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 26.5 | 29.1 [22–36] | +2.6 | +2.6 | 249 |
| Chet Holmgren | UNCERTAIN/QUESTIONABLE | 0.97 | 0.98 | 27.3 | 28.8 [22–36] | +1.5 | +1.5 | 183 |
| Isaiah Hartenstein | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.97 | 20.8 | 21.9 [14–30] | +1.1 | +1.1 | 399 |
| Cason Wallace | UNCERTAIN/QUESTIONABLE | 0.86 | 0.95 | 21.9 | 21.4 [14–30] | -0.6 | -0.6 | 228 |
| Ajay Mitchell | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.95 | 21.1 | 21.1 [13–29] | +0.0 | +0.0 | 94 |
| Jared McCain | LIKELY_ACTIVE/ACTIVE | 0.93 | 0.91 | 16.8 | 17.8 [10–27] | +1.0 | +1.0 | 90 |
| Jaylin Williams | UNCERTAIN/QUESTIONABLE | 0.69 | 0.88 | 15.3 | 17.4 [9–26] | +2.1 | +2.1 | 230 |
| Alex Caruso | LIKELY_ACTIVE/ACTIVE | 0.90 | 0.89 | 15.9 | 16.8 [9–26] | +1.0 | +1.0 | 411 |
| Kenrich Williams | LIKELY_ACTIVE/ACTIVE | 0.91 | 0.85 | 15.0 | 14.9 [6–24] | -0.1 | -0.1 | 402 |
| Josh Dix ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.68 | 11.4 | 13.4 [4–22] | +2.0 | +2.0 | 0 |
| Aday Mara ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.64 | 11.8 | 12.4 [3–21] | +0.6 | +0.6 | 0 |
| Bennett Stirtz ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.39 | 11.4 | 11.7 [5–21] | +0.3 | +0.3 | 0 |
| Brooks Barnhizer | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.75 | 11.9 | 11.1 [4–21] | -0.8 | -0.8 | 40 |

### ORL vs ATL — 2026-10-21T23:00:00Z — Σ(p·min) JRM 241.5 (raw 252.0), frozen 240.1 raw / 240.1 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Paolo Banchero | LIKELY_ACTIVE/ACTIVE | 0.99 | 1.00 | 32.6 | 33.7 [27–39] | +1.0 | +1.0 | 270 |
| Desmond Bane | LIKELY_ACTIVE/ACTIVE | 0.99 | 1.00 | 29.4 | 32.3 [26–39] | +2.9 | +2.9 | 395 |
| Franz Wagner | UNCERTAIN/QUESTIONABLE | 0.93 | 0.97 | 24.0 | 28.1 [21–35] | +4.1 | +4.1 | 324 |
| Jalen Suggs | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 25.9 | 27.4 [20–35] | +1.6 | +1.6 | 268 |
| Wendell Carter Jr. | LIKELY_ACTIVE/ACTIVE | 0.99 | 1.00 | 26.7 | 26.0 [19–34] | -0.7 | -0.7 | 417 |
| Nikola Vucevic | LIKELY_ACTIVE/ACTIVE | 0.91 | 0.93 | 22.3 | 22.6 [15–31] | +0.2 | +0.2 | 500 |
| Tristan da Silva | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 23.2 | 21.2 [14–29] | -2.0 | -2.0 | 151 |
| Jevon Carter | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.85 | 17.5 | 16.7 [9–25] | -0.8 | -0.8 | 425 |
| Goga Bitadze | LIKELY_ACTIVE/ACTIVE | 0.91 | 0.86 | 16.7 | 14.6 [5–24] | -2.1 | -2.1 | 381 |
| Jamal Cain | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.84 | 15.7 | 14.5 [5–24] | -1.1 | -1.1 | 115 |
| Jase Richardson | UNCERTAIN/QUESTIONABLE | 0.46 | 0.54 | 7.9 | 10.1 [3–20] | +2.2 | +2.2 | 54 |
| Colin Castleton | LIKELY_ACTIVE/ACTIVE | 0.65 | 0.59 | 11.0 | 9.7 [3–19] | -1.3 | -1.3 | 45 |
| Alex Morales | LIKELY_ACTIVE/ACTIVE | 0.55 | 0.40 | 8.0 | 7.2 [0–17] | -0.8 | -0.8 | 4 |

### PHI vs NYK — 2026-10-20T23:00:00Z — Σ(p·min) JRM 241.5 (raw 255.6), frozen 273.8 raw / 243.0 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Tyrese Maxey | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 31.1 | 33.3 [27–39] | +2.2 | -1.7 | 387 |
| Jaylen Brown | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 30.1 | 31.8 [25–38] | +1.7 | -2.1 | 452 |
| VJ Edgecombe | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 29.6 | 30.9 [24–37] | +1.3 | -2.4 | 75 |
| Joel Embiid | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.99 | 28.1 | 30.9 [24–37] | +2.8 | -0.7 | 332 |
| LeBron James | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.99 | 27.3 | 30.4 [24–37] | +3.1 | -0.3 | 425 |
| Anfernee Simons | LIKELY_ACTIVE/ACTIVE | 0.77 | 0.90 | 21.4 | 22.7 [15–31] | +1.4 | -1.3 | 424 |
| Kentavious Caldwell-Pope | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.88 | 18.0 | 15.4 [6–24] | -2.6 | -4.9 | 493 |
| Rayan Rupert | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.94 | 18.6 | 13.6 [5–23] | -4.9 | -7.3 | 155 |
| Adem Bona | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.90 | 15.7 | 11.7 [5–21] | -3.9 | -5.9 | 129 |
| Caleb Love | LIKELY_ACTIVE/ACTIVE | 0.62 | 0.72 | 9.8 | 11.7 [5–21] | +2.0 | +0.7 | 49 |
| Labaron Philon Jr. ⚑ | LIKELY_ACTIVE/ACTIVE | 0.77 | 0.74 | 12.3 | 10.9 [4–20] | -1.4 | -3.0 | 0 |
| Justin Edwards | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.75 | 13.0 | 10.4 [3–20] | -2.6 | -4.2 | 107 |
| Jabari Walker | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.48 | 9.7 | 7.0 [0–16] | -2.8 | -4.0 | 251 |

### PHX vs POR — 2026-10-22T02:00:00Z — Σ(p·min) JRM 241.5 (raw 250.5), frozen 270.9 raw / 270.9 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Devin Booker | UNVERIFIED | 0.98 | 0.98 | 34.2 | 34.6 [28–40] | +0.4 | +0.4 | 465 |
| Dillon Brooks | UNVERIFIED | 0.97 | 0.98 | 30.5 | 31.8 [25–38] | +1.4 | +1.4 | 448 |
| Jalen Green | UNVERIFIED | 0.92 | 0.94 | 27.7 | 29.9 [23–36] | +2.2 | +2.2 | 339 |
| Miles Bridges | UNVERIFIED | 0.94 | 0.98 | 27.6 | 27.2 [20–34] | -0.4 | -0.4 | 421 |
| Collin Gillespie | UNVERIFIED | 0.94 | 0.97 | 23.7 | 23.6 [16–31] | -0.1 | -0.1 | 136 |
| Jordan Goodwin | UNVERIFIED | 0.90 | 0.90 | 21.9 | 21.4 [14–30] | -0.6 | -0.6 | 218 |
| Oso Ighodaro | UNCERTAIN/QUESTIONABLE | 0.94 | 0.92 | 21.2 | 20.0 [12–28] | -1.2 | -1.2 | 142 |
| Luke Kennard | UNCERTAIN/QUESTIONABLE | 0.73 | 0.74 | 20.6 | 18.3 [10–27] | -2.3 | -2.3 | 402 |
| Pat Spencer | UNVERIFIED | 0.86 | 0.84 | 20.0 | 16.6 [8–25] | -3.4 | -3.4 | 111 |
| Ryan Dunn | UNVERIFIED | 0.88 | 0.79 | 17.8 | 14.8 [6–24] | -3.0 | -3.0 | 142 |
| Rasheer Fleming | UNVERIFIED | 0.75 | 0.65 | 14.0 | 9.8 [3–19] | -4.2 | -4.2 | 55 |
| Koa Peat ⚑ | UNVERIFIED | 0.51 | 0.35 | 11.4 | 9.6 [3–19] | -1.8 | -1.8 | 0 |
| Duop Reath | UNVERIFIED | 0.63 | 0.18 | 10.5 | 9.0 [2–19] | -1.5 | -1.5 | 146 |
| Jamaree Bouyea | UNVERIFIED | 0.77 | 0.60 | 14.2 | 9.0 [2–18] | -5.2 | -5.2 | 65 |
| Khaman Maluach | UNVERIFIED | 0.70 | 0.57 | 12.4 | 8.4 [1–18] | -4.1 | -4.1 | 46 |

### POR vs PHX — 2026-10-22T02:00:00Z — Σ(p·min) JRM 241.5 (raw 245.0), frozen 233.9 raw / 233.9 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Deni Avdija | UNVERIFIED | 0.97 | 0.99 | 32.7 | 32.7 [27–38] | +0.1 | +0.1 | 425 |
| Toumani Camara | UNVERIFIED | 0.99 | 0.99 | 32.7 | 32.4 [26–39] | -0.3 | -0.3 | 230 |
| Damian Lillard | UNVERIFIED | 0.41 | 0.85 | 29.8 | 32.3 [26–39] | +2.5 | +2.5 | 352 |
| Ja Morant | UNVERIFIED | 0.95 | 0.98 | 27.3 | 29.4 [22–37] | +2.1 | +2.1 | 327 |
| Jrue Holiday | UNCERTAIN/QUESTIONABLE | 0.96 | 0.98 | 28.5 | 29.0 [22–36] | +0.6 | +0.6 | 437 |
| Donovan Clingan | UNVERIFIED | 0.98 | 0.99 | 25.6 | 24.5 [17–32] | -1.1 | -1.1 | 144 |
| Scoot Henderson | UNVERIFIED | 0.96 | 0.98 | 23.5 | 23.1 [15–31] | -0.4 | -0.4 | 158 |
| Robert Williams III | UNVERIFIED | 0.87 | 0.79 | 17.8 | 15.4 [6–24] | -2.4 | -2.4 | 261 |
| Vit Krejci | UNVERIFIED | 0.49 | 0.46 | 14.2 | 14.7 [6–24] | +0.5 | +0.5 | 202 |
| Micah Potter | UNCERTAIN/QUESTIONABLE | 0.66 | 0.83 | 17.1 | 12.7 [4–22] | -4.4 | -4.4 | 111 |
| Branden Carlson | UNVERIFIED | 0.53 | 0.60 | 14.3 | 9.9 [3–19] | -4.3 | -4.3 | 73 |
| John Tonje | UNVERIFIED | 0.28 | 0.34 | 11.4 | 9.1 [2–19] | -2.3 | -2.3 | 5 |
| Sidy Cissoko | UNVERIFIED | 0.55 | 0.49 | 10.5 | 9.0 [2–18] | -1.5 | -1.5 | 106 |
| Chris Youngblood | UNCERTAIN/QUESTIONABLE | 0.27 | 0.13 | 7.1 | 6.4 [0–16] | -0.7 | -0.7 | 32 |
| Yang Hansen | UNVERIFIED | 0.38 | 0.23 | 7.2 | 5.6 [0–15] | -1.6 | -1.6 | 43 |

### SAC vs LAC — 2026-10-22T02:30:00Z — Σ(p·min) JRM 241.5 (raw 244.6), frozen 216.0 raw / 216.0 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Keegan Murray | UNVERIFIED | 0.69 | 0.56 | 32.2 | 34.9 [29–40] | +2.7 | +2.7 | 256 |
| Zach LaVine | UNVERIFIED | 0.92 | 0.84 | 27.0 | 31.7 [25–38] | +4.7 | +4.7 | 400 |
| Domantas Sabonis | UNVERIFIED | 0.94 | 0.96 | 27.3 | 30.9 [24–37] | +3.6 | +3.6 | 436 |
| Precious Achiuwa | UNVERIFIED | 0.97 | 0.99 | 24.1 | 25.6 [18–33] | +1.4 | +1.4 | 393 |
| Nique Clifford | UNVERIFIED | 0.96 | 0.98 | 26.5 | 25.1 [18–33] | -1.4 | -1.4 | 75 |
| De'Andre Hunter | UNVERIFIED | 0.65 | 0.79 | 22.2 | 22.1 [14–30] | -0.1 | -0.1 | 372 |
| Malik Monk | UNCERTAIN/QUESTIONABLE | 0.72 | 0.89 | 18.7 | 21.8 [14–30] | +3.1 | +3.1 | 449 |
| Daeqwon Plowden | UNVERIFIED | 0.94 | 0.96 | 22.3 | 20.9 [13–29] | -1.4 | -1.4 | 38 |
| Leaky Black | UNVERIFIED | 0.54 | 0.78 | 21.9 | 19.7 [12–28] | -2.1 | -2.1 | 41 |
| Darius Acuff Jr. ⚑ | UNVERIFIED | 0.63 | 0.70 | 14.9 | 17.3 [9–26] | +2.3 | +2.3 | 0 |
| Alex Karaban ⚑ | UNVERIFIED | 0.63 | 0.66 | 14.9 | 16.6 [8–25] | +1.7 | +1.7 | 0 |
| Emanuel Sharp ⚑ | UNVERIFIED | 0.63 | 0.69 | 14.9 | 16.6 [8–25] | +1.7 | +1.7 | 0 |
| Jonathan Mogbo | UNVERIFIED | 0.52 | 0.62 | 11.2 | 13.9 [5–23] | +2.7 | +2.7 | 101 |

### SAS vs OKC — 2026-10-21T01:30:00Z — Σ(p·min) JRM 241.5 (raw 260.2), frozen 276.5 raw / 243.3 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Stephon Castle | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 26.7 | 30.0 [23–36] | +3.3 | -0.4 | 150 |
| De'Aaron Fox | LIKELY_ACTIVE/ACTIVE | 0.99 | 1.00 | 27.2 | 29.2 [22–36] | +2.0 | -1.7 | 450 |
| Victor Wembanyama | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 24.6 | 28.3 [21–36] | +3.7 | +0.4 | 182 |
| Devin Vassell | LIKELY_ACTIVE/ACTIVE | 0.99 | 1.00 | 25.5 | 27.6 [20–35] | +2.1 | -1.3 | 370 |
| Julian Champagnie | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 22.6 | 23.4 [16–31] | +0.8 | -2.2 | 256 |
| Keldon Johnson | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.95 | 19.7 | 20.6 [13–29] | +0.8 | -1.9 | 453 |
| Dylan Harper | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.95 | 18.8 | 20.0 [12–28] | +1.3 | -1.3 | 70 |
| Harrison Barnes | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.91 | 18.5 | 19.8 [12–28] | +1.3 | -1.3 | 531 |
| Luke Kornet | LIKELY_ACTIVE/ACTIVE | 0.93 | 0.94 | 17.8 | 16.8 [9–26] | -1.1 | -3.5 | 355 |
| Carter Bryant | LIKELY_ACTIVE/ACTIVE | 0.92 | 0.88 | 14.6 | 12.8 [4–22] | -1.8 | -3.8 | 71 |
| Maliq Brown ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.62 | 10.4 | 9.9 [3–19] | -0.5 | -1.9 | 0 |
| Tarris Reed Jr. ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.62 | 10.9 | 9.6 [3–19] | -1.3 | -2.8 | 0 |
| Ja'Kobi Gillespie ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.59 | 11.1 | 9.4 [2–19] | -1.7 | -3.2 | 0 |
| David Jones Garcia | LIKELY_ACTIVE/ACTIVE | 0.73 | 0.16 | 7.4 | 6.3 [0–16] | -1.0 | -2.0 | 11 |
| Jordan McLaughlin | LIKELY_ACTIVE/ACTIVE | 0.57 | 0.22 | 8.8 | 5.7 [0–15] | -3.1 | -4.3 | 331 |

### TOR vs CHI — 2026-10-21T23:30:00Z — Σ(p·min) JRM 241.5 (raw 244.9), frozen 263.3 raw / 263.3 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Scottie Barnes | LIKELY_ACTIVE/ACTIVE | 0.99 | 1.00 | 31.7 | 32.3 [26–39] | +0.6 | +0.6 | 356 |
| Kawhi Leonard | LIKELY_ACTIVE/ACTIVE | 0.99 | 1.00 | 30.3 | 30.8 [24–37] | +0.5 | +0.5 | 331 |
| RJ Barrett | LIKELY_ACTIVE/ACTIVE | 0.98 | 1.00 | 30.7 | 30.3 [24–37] | -0.4 | -0.4 | 444 |
| Immanuel Quickley | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.99 | 28.5 | 29.7 [22–37] | +1.2 | +1.2 | 394 |
| Jamal Shead | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.96 | 20.4 | 21.0 [13–29] | +0.6 | +0.6 | 157 |
| Collin Murray-Boyles | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.95 | 18.9 | 20.9 [13–29] | +2.0 | +2.0 | 57 |
| Jakob Poeltl | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.97 | 24.1 | 20.2 [13–28] | -3.9 | -3.9 | 428 |
| Ja'Kobe Walter | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.97 | 19.6 | 19.4 [11–28] | -0.3 | -0.3 | 124 |
| Kyle Anderson | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.92 | 19.1 | 13.7 [5–23] | -5.4 | -5.4 | 456 |
| Malachi Smith | LIKELY_ACTIVE/ACTIVE | 0.86 | 0.75 | 16.8 | 12.7 [4–22] | -4.2 | -4.2 | 15 |
| Jaden Bradley ⚑ | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.65 | 10.7 | 9.2 [2–19] | -1.5 | -1.5 | 0 |
| Allen Graves ⚑ | LIKELY_ACTIVE/ACTIVE | 0.74 | 0.63 | 10.8 | 8.7 [2–18] | -2.1 | -2.1 | 0 |
| Jamison Battle | LIKELY_ACTIVE/ACTIVE | 0.65 | 0.58 | 8.2 | 7.0 [0–17] | -1.1 | -1.1 | 119 |
| Trayce Jackson-Davis | LIKELY_ACTIVE/ACTIVE | 0.57 | 0.14 | 7.8 | 6.4 [0–16] | -1.4 | -1.4 | 180 |
| Alijah Martin | LIKELY_ACTIVE/ACTIVE | 0.69 | 0.33 | 7.1 | 5.8 [0–15] | -1.3 | -1.3 | 23 |

### UTA vs MEM — 2026-10-22T00:00:00Z — Σ(p·min) JRM 241.5 (raw 258.6), frozen 266.3 raw / 266.3 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Keyonte George | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 28.1 | 32.1 [25–38] | +3.9 | +3.9 | 196 |
| Lauri Markkanen | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.99 | 30.1 | 31.9 [25–38] | +1.7 | +1.7 | 372 |
| Jaren Jackson Jr. | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.97 | 27.9 | 31.2 [24–38] | +3.3 | +3.3 | 397 |
| Ace Bailey | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 28.6 | 26.9 [20–34] | -1.7 | -1.7 | 72 |
| Kyle Filipowski | UNCERTAIN/QUESTIONABLE | 0.94 | 0.96 | 24.8 | 24.5 [17–32] | -0.3 | -0.3 | 149 |
| Isaiah Collier | LIKELY_ACTIVE/ACTIVE | 0.88 | 0.94 | 24.2 | 24.2 [17–32] | +0.1 | +0.1 | 130 |
| Brice Sensabaugh | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 24.6 | 24.0 [17–32] | -0.7 | -0.7 | 177 |
| Jaxson Hayes | LIKELY_ACTIVE/ACTIVE | 0.94 | 0.89 | 21.4 | 16.8 [9–26] | -4.5 | -4.5 | 434 |
| Svi Mykhailiuk | LIKELY_ACTIVE/ACTIVE | 0.62 | 0.48 | 18.6 | 12.7 [4–22] | -5.9 | -5.9 | 336 |
| Josh Green | LIKELY_ACTIVE/ACTIVE | 0.86 | 0.77 | 14.6 | 11.6 [5–21] | -2.9 | -2.9 | 348 |
| Josh Okogie | LIKELY_ACTIVE/ACTIVE | 0.87 | 0.78 | 16.6 | 11.6 [5–21] | -5.0 | -5.0 | 419 |
| Darryn Peterson ⚑ | LIKELY_ACTIVE/ACTIVE | 0.72 | 0.66 | 13.3 | 10.6 [4–20] | -2.7 | -2.7 | 0 |
| Mo Bamba | LIKELY_ACTIVE/ACTIVE | 0.73 | 0.33 | 15.1 | 9.6 [3–19] | -5.5 | -5.5 | 321 |
| Harrison Ingram | LIKELY_ACTIVE/ACTIVE | 0.60 | 0.25 | 9.0 | 7.1 [0–17] | -1.9 | -1.9 | 12 |

### WAS vs MIL — 2026-10-21T23:00:00Z — Σ(p·min) JRM 241.5 (raw 271.3), frozen 290.4 raw / 243.5 gated

| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Anthony Davis | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.99 | 23.5 | 27.3 [20–35] | +3.8 | -0.7 | 342 |
| Trae Young | LIKELY_ACTIVE/ACTIVE | 0.97 | 0.98 | 20.3 | 27.2 [20–34] | +7.0 | +3.1 | 417 |
| Kyshawn George | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.95 | 19.8 | 24.0 [17–32] | +4.2 | +0.4 | 116 |
| Alex Sarr | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.97 | 19.8 | 23.5 [16–31] | +3.7 | -0.1 | 115 |
| Bilal Coulibaly | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.98 | 21.3 | 22.8 [15–31] | +1.6 | -2.5 | 178 |
| Deandre Ayton | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.97 | 21.1 | 22.3 [15–30] | +1.2 | -2.9 | 399 |
| Will Riley | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.98 | 21.0 | 21.4 [14–30] | +0.4 | -3.7 | 74 |
| Tre Johnson | LIKELY_ACTIVE/ACTIVE | 0.95 | 0.87 | 17.9 | 20.3 [13–29] | +2.4 | -1.0 | 60 |
| Bub Carrington | LIKELY_ACTIVE/ACTIVE | 0.99 | 0.98 | 19.8 | 19.3 [11–28] | -0.4 | -4.2 | 164 |
| Anthony Gill | LIKELY_ACTIVE/ACTIVE | 0.98 | 0.90 | 17.2 | 16.6 [8–25] | -0.6 | -3.9 | 274 |
| Justin Champagnie | LIKELY_ACTIVE/ACTIVE | 0.96 | 0.71 | 16.5 | 15.1 [6–24] | -1.5 | -4.6 | 185 |
| Khris Middleton | LIKELY_ACTIVE/ACTIVE | 0.66 | 0.62 | 16.1 | 12.8 [4–22] | -3.2 | -6.3 | 384 |
| Felix Okpara ⚑ | LIKELY_ACTIVE/ACTIVE | 0.68 | 0.33 | 10.5 | 9.0 [2–18] | -1.5 | -3.5 | 0 |
| Reece Beekman | LIKELY_ACTIVE/ACTIVE | 0.80 | 0.35 | 11.5 | 7.5 [0–17] | -4.0 | -6.2 | 35 |
| Tre Mann | LIKELY_ACTIVE/ACTIVE | 0.57 | 0.15 | 8.4 | 6.4 [0–16] | -2.0 | -3.6 | 234 |

⚑ = fewer than 3 career games in the data (role is prior-driven; shown at Low reliability).

## Largest differences, investigated

| player | team | availability | frozen raw → gated | JRM | Δ vs gated | Δ vs raw | p frozen→JRM | note |
|---|---|---|---|---:|---:|---:|---|---|
| Derrick Jones Jr. | LAC | UNVERIFIED | 24.3 → 33.3 | 25.7 | -7.6 | +1.4 | 0.96→0.98 | the frozen gate scaled the whole team UP (projected below budget); JRM redistributes injured teammates' minutes by rank instead |
| Darius Garland | LAC | UNVERIFIED | 27.9 → 38.3 | 30.8 | -7.5 | +2.9 | 0.96→0.99 | set features raise him (thin competition at his position/level in the available set) |
| Dejounte Murray | NOP | LIKELY_ACTIVE | 28.2 → 20.2 | 27.4 | +7.3 | -0.7 | 0.97→0.99 | the frozen gate scaled the whole team down; JRM keeps his own-history level and takes the minutes from the fringe |
| Anthony Edwards | MIN | LIKELY_ACTIVE | 32.2 → 27.4 | 34.4 | +7.0 | +2.1 | 0.98→0.99 | the frozen gate scaled the whole team down; JRM keeps his own-history level and takes the minutes from the fringe |
| Trae Young | WAS | LIKELY_ACTIVE | 24.2 → 20.3 | 27.2 | +7.0 | +3.1 | 0.97→0.98 | set features raise him (thin competition at his position/level in the available set) |
| Zion Williamson | NOP | LIKELY_ACTIVE | 30.5 → 21.8 | 28.8 | +7.0 | -1.7 | 0.99→0.99 | the frozen gate scaled the whole team down; JRM keeps his own-history level and takes the minutes from the fringe |
| Herbert Jones | NOP | LIKELY_ACTIVE | 26.4 → 18.9 | 25.8 | +6.9 | -0.6 | 0.98→0.98 | the frozen gate scaled the whole team down; JRM keeps his own-history level and takes the minutes from the fringe |
| Trey Murphy III | NOP | LIKELY_ACTIVE | 33.9 → 24.3 | 30.9 | +6.6 | -3.0 | 0.97→0.99 | depth: more higher-level teammates available; rank-aware heads and conservation reduce him |
| Michael Porter Jr. | BKN | LIKELY_ACTIVE | 31.9 → 25.6 | 32.2 | +6.6 | +0.3 | 0.99→0.99 | the frozen gate scaled the whole team down; JRM keeps his own-history level and takes the minutes from the fringe |
| OG Anunoby | NYK | LIKELY_ACTIVE | 34.1 → 27.7 | 34.3 | +6.6 | +0.1 | 0.98→0.99 | the frozen gate scaled the whole team down; JRM keeps his own-history level and takes the minutes from the fringe |
| Ryan Rollins | MIL | LIKELY_ACTIVE | 30.4 → 24.1 | 30.7 | +6.6 | +0.3 | 0.99→0.99 | the frozen gate scaled the whole team down; JRM keeps his own-history level and takes the minutes from the fringe |
| Rui Hachimura | LAC | UNVERIFIED | 23.2 → 31.9 | 25.4 | -6.5 | +2.1 | 0.91→0.98 | the frozen gate scaled the whole team UP (projected below budget); JRM redistributes injured teammates' minutes by rank instead |
| Saddiq Bey | NOP | LIKELY_ACTIVE | 30.8 → 22.1 | 28.5 | +6.5 | -2.3 | 0.99→0.99 | the frozen gate scaled the whole team down; JRM keeps his own-history level and takes the minutes from the fringe |
| Tyler Herro | MIL | LIKELY_ACTIVE | 29.6 → 23.5 | 29.5 | +6.1 | -0.0 | 0.96→0.99 | the frozen gate scaled the whole team down; JRM keeps his own-history level and takes the minutes from the fringe |
| Jalen Brunson | NYK | LIKELY_ACTIVE | 35.0 → 28.4 | 34.4 | +6.0 | -0.6 | 0.98→1.00 | the frozen gate scaled the whole team down; JRM keeps his own-history level and takes the minutes from the fringe |

Established rotation (≥ 20 career games, JRM rank ≤ 8, p ≥ 0.5; n = 188): mean conditional minutes frozen raw 25.98, frozen gated 23.95, JRM 25.75.
No/thin-history players (n = 43): JRM 11.48 vs frozen raw 12.33 (JRM higher by -0.85); p JRM 0.52 vs frozen 0.69.

## Remaining structural issues

* Raw (pre-conservation) JRM sums range 233-277 (SD 10.1; historical opener SD 17, in-season 5.7). Conservation corrections of 15+ minutes: NOP -35.7, WAS -29.8, MEM -28.9, BKN -25.3, HOU -22.3, SAS -18.7; each is spread equally over the team's eligible players (about 1-3 minutes each), is within the historical opener dispersion, and is reported per team above rather than hidden in a scale factor.
* Players with no NBA history (n = 43): JRM 11.48 vs frozen raw 12.33 minutes, p 0.52 vs 0.69. Their dressing probability is unobservable from the historical pool (never-dressed roster members are absent from training); they stay at Low reliability.
* 17% of rows have no injury observation yet (`UNVERIFIED`): the eligibility head is then history-only (Brier 0.079 on 2025-26 vs 0.038 with the report), so participation uncertainty is wide until the reports land; snapshots are re-archived at each report.
* Points reconciliation to the team-points projection (usage scaling) is a separate step and is not part of this minutes shadow.