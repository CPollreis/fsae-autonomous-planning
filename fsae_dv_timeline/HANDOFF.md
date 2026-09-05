# UMSAE Driverless — Research Handoff

Written 2026-09-04. Everything below is either extracted from the official rules PDFs in this
repo or sourced from a benchmark study of 16 Formula Student driverless programs and 6
cross-team subsystem deep dives (all 22 records validated at 100% field coverage).

Open `dv_timeline_comparison.html` in a browser for the interactive version. Rebuild it with
`python3 build_timeline_html.py` after editing any JSON in this folder.

---

## The goal

Program started June 2026. Target: pass Driverless Technical Inspection and the EBS test, and
score all three DV dynamic events at FSAE 2028 — Design 150, Acceleration 75, Skidpad 75,
Autocross 100, for 400 points maximum.

The official SAE roadmap is 2026 Introduction (optional) → 2027-2029 Expansion (optional) →
2030 Full Integration. So June 2028 is exactly two years ahead of the mandate. Confirmed
against `Formula_SAE_Driverless_Implementation_Roadmap_rev8.5.2026.pdf`.

UMSAE already has a running FSAE Electric vehicle, so no EV conversion sits on the critical
path. Caleb is the Driverless System Officer (DA.4.1).

---

## The three findings that should drive planning

### 1. Reliability outranks speed, by a wide margin

Each dynamic event splits into Starting / Completion / Performance points. Acceleration is
25/25/25, Skidpad 25/25/25, Autocross 25/25/50.

**150 of the 250 dynamic points are speed-independent** — awarded for crossing the start line
with all four wheels and completing at least one run. Only 100 depend on being fast. With
Design at 150, a slow but reliable car can score roughly 300 of 400.

Build order, from the practitioner who led Edinburgh's driverless software team 2021-2023 and
won FS-AI twice: **Acceleration → Autocross → Trackdrive → Skidpad**. Skidpad is deceptively
hard despite fixed geometry (9 m minimum turning diameter, 0.125 s per-cone penalties, and
DD.4.3.5.c makes a wrong lap count an outright DNF). EUFS took four years to complete theirs.
His warning: *"If you try and complete all the events at the same time, you probably won't do
any of them."*

### 2. Every fast ramp retrofitted an existing EV

| Team | Months to first DV comp | Notes |
|---|---|---|
| KA-RaceIng (KIT) | 7–8 | Retrofit existing EV |
| e-gnition Hamburg | 9 | 3rd place on debut |
| Chalmers | 10–11 | Onto a running EV — closest analogue to us |
| TUfast (TUM) | 12 | eb015 → db017 |
| DUT Delft + MIT | 12–14 | 3rd at FSG 2019 |
| AMZ (ETH) | 12–18 | Retrofit proven EV |
| KTH | 18–20 | |
| Carnegie Mellon | ~20 | **1st in DV Design at FSAE Michigan 2026** |
| UTFR (Toronto) | 24–30 | Closest peer, see below |
| QUT | 29–31 | Lost ~2 seasons to custom SLAM |
| Monash | ~58 | COVID-distorted |
| MUR, MIT (solo), Cornell | never | See negatives below |

The differentiator is not talent or budget. It is whether vehicle engineering sits on the
critical path, whether the team resists rebuilding solved problems, and whether someone owns
the unglamorous safety hardware.

**Negative results, reported honestly:** MUR Motorsports never achieved an on-vehicle
autonomous run in seven years — their base EV kept failing scrutineering. MIT has no
independent DV competition entry; their own MY27 sponsor packet lists it as a future goal.
Cornell has no driverless program. EUFS's fast 2018 win used IMechE's pre-built shared
ADS-DV platform; their own self-built DV car still is not through scrutineering.

### 3. EBS comes before autonomy, not alongside it

UTFR — Canadian, same winter constraint, same academic calendar — has a fully dated sequence:

- Nov 2023 — EBS validated on bench
- May 2024 — full EBS on vehicle
- Jun 2024 — remote e-stop integrated
- Jul 2024 — system validation
- **Nov 2024 — full autonomous navigation** (12 months after EBS work began)
- 2025 — only team to pass DV tech inspection and run autonomous autocross at FSAE Michigan;
  first North American team in FSG's Driverless Cup, Design Finalist

That ordering is the opposite of a software-heavy team's instinct, and it matches the
rules-derived critical path exactly: DI.1.1 makes inspection plus the EBS test a precondition
for any driverless operation.

**Caveat worth heeding:** UTFR's FSAE Michigan overall finish fell 5th → 10th → 15th → 51st
across 2023-2026 while pushing driverless and 4WD. That is resource contention with the EV
program showing up in results. Since our DV work rides on the EV team's car, agree vehicle
access and shared-member allocation in writing before the winter build.

---

## Engineering gotchas that decide pass/fail

**EBS actuator sizing.** Size on the 200 ms actuation-time-derated force, NOT the static
datasheet force. A published thesis applies a **60% load factor** because hydraulic actuators
cannot deliver rated force inside the DT.3.2.5.a window. Size from the static number and the
failure surfaces during dynamic testing, too late to redesign.

**The real long-lead item is not the LiDAR.** It is the certified PI/TPED pressure tank and
regulator: 4–8 weeks plus certification paperwork, with a 5-year service-life expiry.

**Read DSF.5 before opening CAD.** Every component must appear in the pressure diagram with no
simplification (DSF.5.1.1). Teams that treated it as later paperwork had to redesign to make
their systems documentable. DSF rejections carry escalating penalties (+25/+50/+75 for 3rd/4th/
5th). A KTH master's thesis spent a full 30-credit semester reaching only ISO 26262 Concept
Phase for the EBS alone.

**Architecture is pre-decided by what we have.** A working hydraulic service brake means
pneumatic or pneumo-hydraulic intensifier piggybacking on existing hydraulics.
Electromechanical spring designs mainly exist to dodge pressure-vessel certification.

**Steering.** Derive static and dynamic torque from our own tie-rod offset, scrub radius and
tire friction, with a safety factor plus a dynamic multiplier (worked example: 6.62 → 9.9 →
18.15 Nm). Select on **continuous** duty-cycle capability, never peak. Prefer a passively
back-drivable ball screw or QDD module — it makes DT.2.2 decoupling and DT.2.1.1 manual
steering nearly free. Chalmers used a pneumatic clamp with backlash and only found the
steering-angle error after a full season. Instrument both the actuator and the rack/wheel.

**EBS test safety.** QUT crashed their car during an EBS test in Dec 2024, ending its
competitive life. Build up in stages: bench → circuit → fault injection → dynamic in speed
increments with generous runoff. Never make a full-speed EBS test the first attempt.

**Software.** Do not write custom SLAM. QUT replaced theirs with off-the-shelf `slam_toolbox`
and measured 93% better mapping accuracy and 87% better pose tracking for less work. Use ROS2
`robot_localization` first. Fork `QUT-Motorsport/QUTMS_Driverless`. AMZ's published lesson:
end-to-end latency (~300 ms) became their hard speed limiter — profile early.

---

## The plan

Full version in `umsae_timeline.json` and the "Our 24-month plan" tab.

| Phase | Window | Gate |
|---|---|---|
| 0 · Concept & org | Jun–Aug 2026 | ✓ Complete |
| 1 · Foundations & procurement | Sep–Nov 2026 | Architecture frozen, long-lead ordered, sim loop running |
| 2 · Winter Build I — safety hardware | Dec 2026–Mar 2027 | **EBS bench-validated** |
| 3 · Integration & first motion | Apr–Jun 2027 | **First autonomous motion by May 2027** |
| 4 · Summer testing | Jun–Oct 2027 | Accel + Autocross complete, EBS test passed |
| 5 · Winter Build II & submissions | Nov 2027–Mar 2028 | NoI, DSF, Vehicle Status Video in |
| 6 · Final validation | Apr–Jun 2028 | Compete |

Built backwards from **first autonomous motion by May 2027**, because summer 2027 is the only
complete outdoor testing season before the target. Winnipeg gives roughly 33 usable outdoor
weeks total before June 2028, and 24 of them are in that one window — which is also when
member availability is worst (co-ops, internships). Commit a named summer crew before April 2027.

At ~6 months from Phase 1 concept, the EBS gate sits at the **aggressive end** of the 6–9 month
cross-team range. If EBS is the only thing slipping, pull people onto it from software.

**De-scope ladder:** drop speed tuning → drop Skidpad → drop Autocross, keeping Acceleration.
Every step still banks points. Floor case is inspection + EBS test + one Acceleration run =
50 dynamic points plus up to 150 Design, and it establishes the team for 2029-2030.
**Never drop inspection or the EBS test** — without them the car cannot legally move and the
entry scores zero dynamic points.

---

## Open items

**The staffing gap is the highest-leverage fix.** The org chart
(`dv_implementation.drawio`, "DV software" page) has no owner for the Driverless System Brake / EBS, and no
owner for the DV electrical safety chain (DSMS, three DSSI, shutdown circuit relays per DT.4,
RSS integration). Those gate scrutineering and need mechanical and electrical students, not
more software members.

**Next 30 days:**
1. Order the Remote Stop System — mandated Gross-Funk hardware, no substitute, gates everything
2. Order the certified PI/TPED pressure tank and regulator
3. Recruit an EBS owner and a DV electrical safety owner
4. Read DT.3 and DSF.5 before starting EBS CAD
5. Select EBS architecture and start detailed design
6. Order LiDAR / compute / IMU-GNSS (Velodyne Puck discontinued; Jetson up to +101% since Jul 2026)
7. Stand up eufs_sim + Docker + CI so software progresses all winter without the car
8. Agree vehicle access terms with the EV team

**Assumptions to confirm:** exact FSAE 2028 dates; 2028 Notice of Intent deadline (organizers
may cap DV entries and screen on it, so submit early); indoor shop space year-round; access to
a paved lot large enough for Acceleration (75 m + runout) and Skidpad geometry May–October.

**Known gaps in the research:** no team publishes a total EBS or steering program cost, or a
clean concept-to-passing-test duration — those figures are synthesized estimates, labelled as
such. No source reports a measured on-track EBS deceleration/reaction-time pair. Two research
agents hit the session web-search cap late and compensated with direct PDF extraction, so a
few planned lookups did not run. Uncertain values are marked `[uncertain]` in the JSON rather
than smoothed over.
