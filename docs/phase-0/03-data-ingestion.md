# Phase 0: Data Ingestion

**Files:** [`src/data/ingest.py`](../../src/data/ingest.py),
[`sources/fastf1.py`](../../src/data/sources/fastf1.py), [`sources/openf1.py`](../../src/data/sources/openf1.py),
[`cleaning/tyre_labels.py`](../../src/data/cleaning/tyre_labels.py), [`cleaning/assemble.py`](../../src/data/cleaning/assemble.py),
[`cleaning/lap_flags.py`](../../src/data/cleaning/lap_flags.py), [`cleaning/quality.py`](../../src/data/cleaning/quality.py),
[`spec/frames.py`](../../src/data/spec/frames.py), [`storage/frozen.py`](../../src/data/storage/frozen.py)

---

## Purpose

Ingest reads every race in `races.yaml` from its raw files, turns it into one common format, refuses races that are
too incomplete, and freezes the result to `data/interim/<race id>/`. After that, calibration needs neither the raw
files nor the network, and two sources look the same to it.

Two sources are needed because neither covers everything:

| Source | Races | Why |
|---|---|---|
| FastF1 cache (`data/raw/`) | 47: 2021, 2022, and 2023 Silverstone, Spa, Monza | Cached before F1's archive started asking for a login |
| OpenF1 JSON (`data/raw/openf1/<year>/<session_key>_*/`) | 66: the rest of 2023, 2024, 2025 | Free, no login |

```
python -m src.data.ingest                  # every race; skips the ones that are up to date
python -m src.data.ingest --race 2024_spa  # one race
python -m src.data.ingest --force          # rebuild even when up to date
```

It prints one line per race built and exits 1 if any race failed, after trying all of them.

---

## The Common Format

`RaceFrames` (in `spec/frames.py`) is what both readers must produce: three tables plus the race length.

### `laps`: one row per car and lap

| Column | Type | Meaning |
|---|---|---|
| `driver`, `driver_number` | string, int | Three-letter code and car number |
| `lap` | int | Lap number, 1 to `race_laps` |
| `lap_time_s`, `sector1_s` - `sector3_s` | float | Times in seconds; NaN when unknown |
| `lap_start_s`, `lap_end_s` | float | Seconds from the start of the data feed |
| `stint`, `compound`, `tyre_age` | Int, string, Int | Tyre set number, `SOFT` ... `WET` or `UNKNOWN`, laps on this tyre including this one |
| `label` | string | How far the tyre columns can be trusted (below) |
| `is_in_lap`, `is_out_lap` | bool | Lap ends in the pit lane / starts from it (never lap 1) |
| `is_accurate` | bool | Sectors add up to the lap time (within 0.01 s), not lap 1, not an in- or out-lap |
| `track_status` | string | Every status code active during the lap, concatenated (`"1"`, `"14"`, ...); empty if the lap's times are unknown |

### `weather` and `track_status`

`weather`: `time_s`, air and track temperature, humidity, wind speed, `rainfall` (bool), one row per sample.
`track_status`: `time_s` and `code`, one row per change, using FastF1's codes: `1` clear, `2` yellow, `4` safety car,
`5` red, `6` VSC, `7` VSC ending.

`enforce_format` keeps exactly these columns, casts them, sorts them and refuses a repeated (car, lap). A reader that
drifts from the format fails here, not later.

---

## Reading FastF1

`fastf1.read_race` opens the cache in **offline mode**: a race that is not cached fails instead of trying to
download. Two guards:

- FastF1 matches event names loosely, so a typo could load another race. The loaded event name must equal `event`.
- A session without laps or weather is refused.

FastF1 already gives lap times, sectors, stints and tyre life per lap. A compound outside the five known ones becomes
`UNKNOWN` with label `missing`; every other lap is `raw`.

---

## Reading OpenF1

OpenF1 gives raw endpoints (`laps`, `stints`, `pit`, `race_control`, `weather`, `drivers`, `session_result`), so more
has to be rebuilt.

### Times

All times are seconds from the feed start (the earliest weather or race control timestamp). OpenF1 has no start time
for lap 1, and after a lap-1 red flag it gives the restart time (2024 Monaco), so every lap 1 starts at the first
`SESSION STARTED` message. A lap ends when the same car's next lap starts. An in-lap is a lap followed by an out-lap,
or listed in `pit`.

### Track status from race control

`track_status(messages, feed_start)` replays race control messages to rebuild FastF1's codes: `SAFETY CAR DEPLOYED`
sets 4, `VIRTUAL SAFETY CAR DEPLOYED` 6, `... ENDING` 7, a red flag 5, `TRACK CLEAR` 1. A race that starts behind the
safety car is 4 from `SESSION STARTED` until the rolling start. Sector yellows give 2 while no neutralisation is
active. A row is written only when the code changes.

### Tyre labels

OpenF1 reports stints (first lap, last lap, compound, age at start), not tyres per lap. `label_laps` turns them into
one compound and age per lap and labels how far each can be trusted:

| Label | Meaning | Used by calibration? |
|---|---|---|
| `raw` | Stint as reported, confirmed by a pit-out | Yes |
| `shifted` | The stint began one lap early and was moved to the pit-out lap | Yes |
| `repaired` | Changed by a named repair in `races.yaml` | Yes |
| `suspect` | A stint change with no pit stop, or a stop with no stint change | No |
| `missing` | No stint covers the lap, or the compound is unknown | No |

The steps:

1. **Drop empty stints** (last lap before first lap), unless a pit stop on both sides shows they were real.
2. **Merge continuations**: two stints on the same compound, back to back, whose ages run on, with no stop between,
   are one stint.
3. **Match stint starts to pit-outs.** Where the pit boxes come before the timing line (Monaco, Montreal, Melbourne),
   OpenF1 starts a stint one lap early. `match_boundaries` pairs each stint start with a pit-out on the same or the
   next lap by dynamic programming: keep the order, maximise the pairs, then minimise the shifts. A start with no
   pit-out makes both stints `suspect`; a pit-out with no start makes the rest of its stint `suspect`.
4. **Age**: $\text{age} = \text{age at start} + \text{lap} - \text{stint start} + 1$, so the first lap on a new tyre is age 1.

The `opening_compound` repair handles one known fault (2025 Spa): stints that begin before a car's first pit-out
cannot be real, because it had no stop, so they are removed and the opening stint runs to the first stop.

---

## Finishing and Checking

`build_frames` is shared by both readers. It drops laps after `race_laps` (counted as `dropped_laps`), sets
`is_accurate`, and sets each lap's `track_status` to every code that overlapped the lap.

`check_race` then summarises the race and refuses it if it breaks a threshold of `ingest.yaml` (fewer than 15 cars,
under 75% known tyres, over 20% missing times, over 25% suspect labels). A `frequency_only` race is summarised but
never refused.

---

## Freezing

Each race is written to `data/interim/<race id>/`:

| File | Content |
|---|---|
| `laps.parquet`, `weather.parquet`, `track_status.parquet` | The three tables |
| `manifest.json` | The race's identity (config version, id, circuit, year, source, event or session key, role, repairs, tolerance), FastF1 version, `race_laps`, `dropped_laps`, row counts, a SHA-256 of each table, and the summary |

> [!NOTE]
> The manifest is deleted first and written **last**, so an interrupted run never looks finished. A race is up to
> date when its manifest exists, all three tables exist, and every identity field matches the current config and
> `races.yaml`. Changing a race's role or repairs, or raising `version`, rebuilds it.

The hash is taken over the table's CSV text, not the parquet bytes, so it does not change with the parquet library.

`load_race(race_id, interim_dir)` reads a frozen race back; it fails with "run python -m src.data.ingest" if the
manifest is missing. Calibration uses only this function to reach race data.
