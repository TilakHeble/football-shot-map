# Build the Tableau dashboard (step by step)

This folder has everything you need to rebuild the shot analysis in **Tableau Public**:

| File | What it is |
|---|---|
| `leverkusen_2023_24_shots.csv` | 916 rows, one per shot in Leverkusen's 34 league matches (both teams). Exported by `sql/10_tableau_shots.sql` |
| `pitch_half_vertical.png` | Background image of the attacking half, goal at the top. Covers **exactly** 0–80 across × 60–120 up the pitch (StatsBomb coordinates) |

Re-create both with `python -m src.export_tableau`.

**Time:** about 1.5–2 hours the first time.
**You'll practise:** calculated fields, parameters, background images, table calculations (running totals), reference lines and dashboard layout. These are the Tableau skills football job ads ask for.

> Use the free **Tableau Public desktop app** (Windows/Mac, from public.tableau.com), not the browser
> editor. Background images (Step 4) need the desktop app.

---

## Step 1: Connect the data

1. Open Tableau Public → **Connect → Text file** → choose `leverkusen_2023_24_shots.csv`.
2. On the Data Source page, check the types: `match_date` = Date, `x`, `y`, `xg`, `distance_m`, `angle_deg` = Number (decimal).
3. Top right: **Filters → Add → Team → Bayer Leverkusen**. This data source filter keeps only Leverkusen's shots everywhere.
4. Go to Sheet 1.
5. In the Data pane, drag `Matchday`, `Minute`, `Period` up from Measures into Dimensions. They're labels, not things to add up.

## Step 2: Calculated fields

Create each one with **Analysis → Create Calculated Field**. Names in **bold**:

```
NP Shots          SUM(IF [Is Penalty] = 0 THEN 1 END)
NP Goals          SUM(IF [Is Penalty] = 0 THEN [Is Goal] END)
npxG              SUM(IF [Is Penalty] = 0 THEN [Xg] END)
npxG per Shot     [npxG] / [NP Shots]
Goals - xG        [NP Goals] - [npxG]
Luck SD           SQRT(SUM(IF [Is Penalty] = 0 THEN [Xg] * (1 - [Xg]) END))
z-score           [Goals - xG] / [Luck SD]
Result            IF [Is Goal] = 1 THEN "Goal" ELSE "No goal" END
Across Pitch      [Y]
Up Pitch          [X]
```

`Luck SD` and `z-score` are the "how much is luck?" check from the README. Each shot is treated as
a coin flip with probability = its xG, so the spread of goals is √Σ xG(1 − xG).

## Step 3: A player parameter

1. Right-click `Player` → **Create → Parameter**. Name it **Selected Player** and set *Current value* to *Florian Wirtz*. Click OK.
2. Right-click the parameter → **Show Parameter**.
3. Create one more calculated field:

```
Is Selected       [Player] = [Selected Player]
```

You'll use `Is Selected` as a filter on the player sheets, and to highlight the selected player in the squad chart.

## Step 4: Sheet "Shot map"

1. Drag **Across Pitch** to Columns and **Up Pitch** to Rows.
2. **Analysis → uncheck Aggregate Measures**, so you get one mark per shot.
3. Drag **Is Selected** to Filters → tick **True**.
4. Marks card → **Circle**. Drag **Xg** to Size and **Result** to Color. Set the colours: Goal = `#2a78d6` (blue), No goal = `#a3a29c` (grey), with opacity ~80%.
5. Drag `Opponent`, `Match Date`, `Minute`, `Xg`, `Outcome` and `Body Part` to Tooltip, then edit the tooltip text to read nicely.
6. **Map → Background Images → (your data source) → Add Image**:
   - File: `pitch_half_vertical.png`
   - X Field: **Across Pitch**, Left **0**, Right **80**
   - Y Field: **Up Pitch**, Bottom **60**, Top **120**
7. Fix the axes so the pitch doesn't stretch: right-click each axis → **Edit Axis → Fixed**:
   - Across Pitch: 0 to 80
   - Up Pitch: **80 to 120**. This zooms into the final third; the image still lines up.

   Then right-click each axis → untick **Show Header**.
8. Check: for Wirtz you should see 71 circles with 11 blue. All the blue in-box ones should sit inside the drawn box.

## Step 5: Sheet "KPIs"

1. Drag **Is Selected** to Filters → True.
2. Drag **Measure Values** to Text, then keep only these in the Measure Values shelf:
   CNT(Shot Id) (rename *Shots*), SUM(Is Goal) (rename *Goals*), npxG, Goals - xG, npxG per Shot.
3. Drag **Measure Names** to Columns.
4. Format: font size ~24 for values; numbers to 1–2 decimals (right-click → Format).
5. Check against the README: **71 shots, 11 goals, 7.69 npxG, +2.31, 0.11**.

## Step 6: Sheet "Season"

1. Drag **Matchday** to Columns, then right-click it → **Continuous**.
2. Drag **Measure Values** to Rows, and keep only **NP Goals** and **npxG**.
3. Drag **Measure Names** to Color: NP Goals = `#2a78d6`, npxG = `#eb6834`.
4. Right-click Measure Values on Rows → **Quick Table Calculation → Running Total**.
5. Marks card → **Line**, then click Path → **Step**.
6. Drag **Is Selected** to Filters → True. Add `Opponent` to Tooltip.
7. Check: the lines finish at **10 NP goals and 7.69 npxG**, with the big jump at matchday 29 (Werder Bremen).

> Matchdays where the player didn't shoot have no row, so the step simply carries on flat. That's the
> correct behaviour for a running total.

## Step 7: Sheet "Squad finishing"

Don't filter this sheet by player: it shows the whole squad.

1. Drag **npxG** to Columns and **Goals - xG** to Rows.
2. Drag **Player** to Detail and to Label.
3. Drag **NP Shots** to Filters → **At least 15**.
4. Drag **Is Selected** to Color: True = `#2a78d6`, False = `#a3a29c`.
5. **Analytics** pane → drag **Reference Line** onto the Goals - xG axis → Value: **Constant 0**, Label: "goals = xG". Players above the line scored more than their chances suggested.
6. Add **z-score** and **NP Shots** to Tooltip.
7. Check: Grimaldo sits highest (+4.79, z = 2.43), Wirtz is second (+2.31) and Boniface is lowest (−2.84).

## Step 8: Sheet "Squad table"

1. Drag **Player** to Rows.
2. Drag **Measure Values** to Text, keeping: NP Shots, NP Goals, npxG, Goals - xG, z-score.
3. Drag **Measure Names** to Columns.
4. Drag **NP Shots** to Filters → at least 15. Sort Player by npxG, descending.

## Step 9: Dashboard

1. **New Dashboard**. Size: **Fixed, 1200 × 1000**, or Automatic.
2. Layout (use a Vertical container, then Horizontal ones inside it):
   - **Title:** "Bayer Leverkusen 2023/24: shooting and finishing" + the *Selected Player* parameter control (top right)
   - **KPIs** across the top
   - **Shot map** (left) | **Season** (right)
   - **Squad finishing** (left) | **Squad table** (right)
   - Small text at the bottom: "Data: StatsBomb Open Data · NP = non-penalty · z-score: |z| > 2 is unusual"
3. Hide the sheet titles you don't need, and give each chart a short heading in a text box.
4. Optional: **Dashboard → Actions → Add Action → Change Parameter**. Source: Squad finishing. Target parameter: Selected Player. Field: Player. Now clicking a dot switches the whole dashboard to that player.

## Step 10: Publish

1. **File → Save to Tableau Public** and sign in. Give it a clear name, e.g. *Leverkusen 2023-24 Shots & xG*.
2. On your Tableau Public profile, add a short description and the GitHub link.
3. Add the Tableau link to the repo README (Dashboards section) and to your CV.

## Final check before sharing

Pick three players and compare the dashboard with `python run.py --player "<name>"`:

| Player | Shots | Goals | NP goals | npxG | Goals − xG | z |
|---|---:|---:|---:|---:|---:|---:|
| Florian Wirtz | 71 | 11 | 10 | 7.69 | +2.31 | +0.96 |
| Alejandro Grimaldo García | 71 | 10 | 10 | 5.21 | +4.79 | +2.43 |
| Victor Okoh Boniface | 81 | 14 | 10 | 12.84 | −2.84 | −0.97 |

If anything differs, the usual culprits are a missing *Is Penalty = 0* condition, or the data source filter on Team.
