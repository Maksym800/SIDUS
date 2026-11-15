# Crew health monitor

A Streamlit app in which astronauts record their own vital signs and get an
early warning when something drifts away from their personal norm. Every
astronaut first stores a baseline measured on Earth; later readings are
compared with it and with general limits, and a rule engine written in C
turns the result into suspected conditions ("Suspected tachycardia" /
"Підозра на тахікардію") shown on a body map.

The app is a study project. It is not a medical device: the thresholds are
screening values that a flight surgeon would have to review.

## Run it

You need Python 3.11 or newer and a C compiler (gcc or clang; on Windows
install the 64-bit MinGW-w64 gcc and put it on the PATH).

```
pip install -r requirements.txt
python -m backend.diagnosis.build    # compiles the C engine
streamlit run app.py
```

Start the app from the project folder, so that `.streamlit/config.toml`
(the colours) is picked up. The build step is optional: the app compiles
the engine itself on first start when a compiler is on the PATH. If the
engine cannot be built, everything except new diagnoses keeps working. The
astronaut screen then shows a setup panel (`frontend/engine_help.py`) with
the install command for your system (winget on Windows, `xcode-select` on
macOS, `apt` on Linux) and a "Check again and build" button, so no restart
is needed after installing a compiler.

Optional sample crew with a few weeks of history:

```
python -m data.seed_demo
```

Tests (standard `unittest`, nothing to install):

```
python -m unittest discover -s tests -v
```

The data is stored in `astro_health.db` next to the project. Set the
`ASTRO_HEALTH_DB` environment variable to keep it somewhere else.

## Who owns what

Each file belongs to one of four roles and says so in its first lines.

| Role | Tools | Files |
|---|---|---|
| Data engineer | Pandas, SQLite | `data/catalog.py` (metric dictionary), `data/db.py` (schema), `data/repository.py` (all queries), `data/seed_demo.py`, `tests/test_data.py` |
| Backend developer 1: diagnosis engine | C, NumPy, Pandas | `backend/diagnosis/diagnosis.c`, `diagnosis.h` (the rules), `build.py` (compiles them), `engine.py` (ctypes and NumPy bridge), `knowledge_base.py` (texts of every diagnosis in both languages), `service.py` (diagnose and store), `tests/test_diagnosis.py` |
| Backend developer 2: analytics | NumPy, Statistics, Pandas | `backend/analytics/flight.py` (flight day and stage), `freshness.py` (24-hour check), `deviations.py` (change against baseline, trends), `history.py` (calendar summaries), `workouts.py`, `coordination.py` (scoring of the test and progress across tests), `export.py` (CSV tables for the doctor), `units.py`, `tests/test_analytics.py` |
| Frontend developer | Streamlit | `app.py`, everything in `frontend/`, `.streamlit/config.toml`, `assets/`, `tests/test_frontend_texts.py` |

Shared by the team: `README.md`, `requirements.txt`, `.gitignore`,
`backend/__init__.py`, `tests/__init__.py`.

How the layers talk to each other:

```
frontend (Streamlit screens)
   |-- data.repository ............ read and write SQLite, returns DataFrames
   |-- backend.diagnosis.service .. diagnose an entry, store the result
   |        `-- engine.py --ctypes--> libdiagnosis (diagnosis.c)
   `-- backend.analytics .......... flight day, staleness, trends, calendars, scoring
```

Only the listed tools are used: Python with its standard library (which
includes `sqlite3`, `statistics` and `ctypes`, the bridge to C), pandas,
NumPy, Streamlit and C. The one exception is the coordination game: a
browser game has to run in the browser, so
`frontend/components/coordination_game/index.html` contains JavaScript.
It only draws the game and records raw samples; the result is computed in
Python (`backend/analytics/coordination.py`).

## Screens

- **Profile menu** (opens first): pick a profile, no password. An
  exclamation mark marks a profile whose data is older than 24 hours.
  The mission environment (Earth, Mars, Moon, Deep space, Orbit) and the
  language toggle (English / Ukrainian) are in the top right corner of
  every screen; both choices are remembered.
- **Profile creation**: name, age, flight start date and the baseline
  measured on Earth. Vision is not asked here. The coordination test can
  be taken on the spot or the value typed by hand.
- **Astronaut menu**: name top left; body map on the left with zones in
  grey `#8b93a7` (normal), yellow `#e9c46a` (requires caution) or red
  `#e65c4f` (critical); suspected conditions with explanations on the
  right; buttons for editing metrics, the coordination test and the
  history calendar; workouts at the bottom (reminder with two answers and
  a calendar of completed workouts).
- **Edit metrics**: the form starts from the current values. Saving adds a
  new entry with the current date and time; nothing is overwritten.
- **History calendar**: click a day to see every entry of that day with
  its time, the diagnoses determined for it (each with its own time and
  environment) and all metrics.
  Under the calendar, two CSV downloads (all metrics, all diagnoses) for
  the flight surgeon.
- **Coordination test**: keep the cursor on a small spaceship for 30
  seconds; the result is the percentage of time on the ship. Saved results
  are charted over time (with a 3-test running average and the Earth
  baseline) below the game.

## The anatomy picture

`assets/anatomy.png` is the project's line drawing of the human body,
already prepared for the dark theme: transparent background, lines in the
accent colour `#9cb8bf`, a faint tint inside the body. The untouched drawing
is kept in `assets/anatomy_original.png`. When a zone is flagged, its marker
turns yellow `#e9c46a` or red `#e65c4f` (pulsing); a whole-body problem
(fever, radiation) makes the outline of the figure glow.

The body map uses the first of `anatomy.png`, `.jpg`, `.jpeg`, `.webp`,
`.svg` that exists in `assets/`. A replacement picture should have a
transparent background and light lines (a black-on-white drawing would
disappear into the dark page). The markers are placed with percentages of
the picture's width and height in `ZONE_LAYOUT` at the top of
`frontend/body_map.py`; the shipped values are calibrated for the shipped
picture (head and eyes on the skull, neck vessels, lungs, heart, liver as
"metabolism", spleen as "immune", hip joints as "bones", thighs as
"muscles"). With another picture, adjust the numbers until the markers sit
in the right places.

## Metrics

Defined once in `data/catalog.py`; the database columns and both forms are
generated from that list.

| Metric | Stored as | Unit |
|---|---|---|
| Mass | `mass_kg` | kg |
| Heart rate | `heart_rate_bpm` | bpm |
| Blood pressure | `bp_systolic`, `bp_diastolic` | mmHg |
| Heart rhythm and variability | `ecg_rhythm` (regular / occasional irregular beats / persistent arrhythmia), `hrv_rmssd_ms` | ms |
| Blood flow and vessels | `blood_flow_cm_s` (jugular vein), `vascular_condition` (normal / stagnant or reversed flow / signs of a clot) | cm/s |
| Vision sharp and clear | `vision_clear` (yes / no, not part of the baseline) | |
| Sleep | `sleep_hours`, `sleep_efficiency_pct` | h, % |
| Muscle | `muscle_thickness_mm`, `muscle_structure` (normal / moderate / pronounced changes) | mm |
| Body temperature | `body_temp_c` | °C |
| Saturation | `spo2_pct` | % |
| Coordination and reaction speed | `coordination_pct` (test result or typed by hand) | % |
| Blood glucose | `glucose_mmol_l` (can be typed in mg/dL) | mmol/L |
| Stress and immunity | `cortisol_nmol_l`, `viral_activation` (noticed or not) | nmol/L |
| Calcium and bone resorption | `calcium_mmol_l` (blood), `bone_resorption_ntx` (urine) | mmol/L, nmol BCE/mmol creatinine |
| Mood and stress | `mood_score`, `stress_score` | 1 to 10 |
| Radiation | `radiation_total_msv`, `neutron_rate_usv_h` | mSv, µSv/h |

To add a metric: add it to `METRICS` in `data/catalog.py`, to the
`MetricIndex` enum and `METRIC_NAMES` in the C files, and give it a label
in `frontend/i18n.py`. The database gets the new column on the next start
and the tests report anything that was forgotten.

## Diagnosis rules

All rules are in `backend/diagnosis/diagnosis.c`. "High" rules fire at the
threshold or above, "low" rules below it. A value that was not measured
never fires a rule. Where two numbers are given in brackets, the second
applies in weightlessness (orbit, deep space); Mars and the Moon lie in
between, in proportion to the missing gravity.

| Suspected condition | Zone | Requires caution | Critical |
|---|---|---|---|
| Tachycardia | heart | pulse ≥ 100, or ≥ 25 above baseline | ≥ 130 |
| Bradycardia | heart | ≥ 20 below baseline, or < 50 and ≥ 8 below baseline | < 40 |
| Arterial hypertension | heart | ≥ 135/85, or +20 systolic / +15 diastolic over baseline | ≥ 160/100 |
| Arterial hypotension | heart | < 90/55, or systolic ≥ 20 below baseline | < 80/45 |
| Arrhythmia | heart | occasional irregular beats | persistent arrhythmia |
| Autonomic strain (low HRV) | heart | < 70 % of baseline or < 20 ms | < 50 % of baseline or < 10 ms |
| Venous congestion, thrombosis risk | neck | stagnant or reversed flow, or velocity down ≥ 40 % (30 %) | signs of a clot, or velocity down ≥ 70 % (60 %) |
| SANS (below Earth gravity only) | eyes | vision not clear | vision not clear with stagnant flow or velocity down ≥ 30 % |
| Visual impairment (Earth only) | eyes | vision not clear | |
| Sleep disorder | head | < 6 h, efficiency < 85 %, or ≥ 2 h below baseline | < 4 h or efficiency < 70 % |
| Muscle atrophy | muscles | thickness down ≥ 10 % (7 %) or moderate changes | down ≥ 20 % (15 %) or pronounced changes |
| Fever | whole body | ≥ 37.5 °C, or ≥ 1.0 °C above baseline | ≥ 38.5 °C |
| Hypothermia | whole body | < 35.5 °C | < 35.0 °C |
| Hypoxemia | lungs | SpO₂ < 95 %, or ≥ 4 points below baseline | < 90 % |
| Sensorimotor impairment | head | coordination down ≥ 15 % (25 % in the first 3 days of weightlessness) | down ≥ 30 % (45 %) |
| Hypoglycemia | metabolism | < 3.9 mmol/L | < 3.0 |
| Hyperglycemia | metabolism | ≥ 7.8 mmol/L | ≥ 11.1 |
| Stress-related immune weakening | immune | cortisol ≥ 1.5 × baseline or ≥ 700 nmol/L | ≥ 2 × baseline or ≥ 1000 |
| Reactivation of latent viruses | immune | viral activation noticed | with temperature ≥ 37.5 °C |
| Accelerated bone loss | bones | resorption marker up ≥ 50 % (30 %) | up ≥ 100 % (70 %) |
| Hypercalcemia | bones | ≥ 2.65 mmol/L | ≥ 3.00 |
| Hypocalcemia | bones | < 2.10 mmol/L | < 1.90 |
| Psycho-emotional strain | head | mood ≤ 4 or stress ≥ 7 | mood ≤ 2 or stress ≥ 9 |
| Excessive radiation exposure | whole body | total ≥ 300 mSv, or mission average ≥ 1.5 × the typical daily dose | ≥ 600 mSv, or ≥ 3 × typical |
| Acute radiation hazard | whole body | neutron dose rate at the environment's caution level | at its critical level |
| Energy deficit (mass loss) | metabolism | mass down ≥ 5 % | down ≥ 10 % |

What the mission environment changes:

| Environment | Gravity (g) | Typical dose (mSv/day) | Neutron rate caution / critical (µSv/h) |
|---|---|---|---|
| Earth | 1.00 | 0.01 | 0.5 / 2 |
| Mars | 0.38 | 0.67 | 4 / 12 |
| Moon | 0.17 | 1.37 | 25 / 75 |
| Deep space | 0 | 1.80 | 5 / 15 |
| Orbit | 0 | 0.70 | 12 / 36 |

The mission-average dose rule is not applied on Earth or in the first week
of a flight. The neutron thresholds are rough multiples of the neutron
share of each radiation field and are the first numbers to replace with
real dosimetry guidance.

To add a rule: write a `rule_...` function in `diagnosis.c`, add it to the
`DiagnosisCode` enum and the `RULES` table, add its texts to
`knowledge_base.py`, rebuild and run the tests.

### Where the numbers come from

Clinical limits (pulse, blood pressure, temperature, SpO₂, glucose,
calcium) are the usual adult reference ranges. The spaceflight-specific
values follow published findings:

- Career radiation limit of 600 mSv: NASA-STD-3001, Volume 1.
- Dose rates: Zeitlin et al., *Science* 2013 and Hassler et al., *Science*
  2014 (Mars Science Laboratory RAD, about 1.8 mSv/day in cruise and
  0.64–0.67 mSv/day on the surface of Mars); Zhang et al., *Science
  Advances* 2020 (Chang'E-4, about 1.37 mSv/day on the lunar surface);
  about 0.4–1.0 mSv/day on the International Space Station.
- Stagnant or reversed jugular flow in 6 of 11 crew members and a clot
  found in flight: Marshall-Goebel et al., *JAMA Network Open* 2019.
- Reactivation of latent herpesviruses in more than half of crew members:
  Rooney et al., *Frontiers in Microbiology* 2019.
- Bone loss of about 1–1.5 % a month in weight-bearing bones: Lang et al.,
  *Journal of Bone and Mineral Research* 2004.
- SANS: Lee et al., *npj Microgravity* 2020.

## Design

Background `#15323d`, text `#f2efe9`, buttons `#52b788`, accents `#9cb8bf`.
The base colours are set in `.streamlit/config.toml`; everything the app
draws itself is styled in `frontend/theme.py`. All interface texts in both
languages are in `frontend/i18n.py`; the texts of the diagnoses are in
`backend/diagnosis/knowledge_base.py`.

## Still open

- **Clinical review of the thresholds.** The rules and the per-environment
  profiles are documented above with their sources, but they are screening
  values. The neutron dose-rate thresholds in particular are rough
  multiples and the first numbers a flight surgeon should replace.
- **Reminders by push or email** are not built: they need a notification
  service outside the allowed libraries. The profile menu's exclamation
  mark and the warning on the astronaut screen cover the 24-hour rule
  inside the app.
- **PDF export** is not built (no PDF library is allowed); CSV is.
- **Windows:** `build.py` looks for MinGW-w64 gcc and produces
  `libdiagnosis.dll`; this has not been run on a Windows machine yet.
- **Manual run-through in a live Streamlit server** of every screen and
  scenario. The tests cover the backend and the interface texts; the
  screens themselves still need clicking through.
