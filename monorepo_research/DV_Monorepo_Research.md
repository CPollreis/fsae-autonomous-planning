# FSAE / Formula Student Driverless Monorepo Research

Research for the UMSAE driverless team: what other teams use, common patterns, and a reference monorepo structure for a ROS2 autonomous system. Compiled July 2026 from direct inspection of public repos (shallow clones + GitHub API) plus targeted search.

**How to read this doc:** Section 1 covers the teams from your spreadsheet. Section 2 covers additional driverless teams found during research. Section 3 lists community resources (simulators, datasets, tools) you can use directly. Section 4 distills the common patterns. Section 5 is a reference monorepo structure. Section 6 is recommendations and the design decisions left to you.

---

## TL;DR

- **Best single reference for your monorepo: QUT Motorsport's `QUTMS_Driverless`** (public, active, ROS2 Jazzy, competition-proven, docker-first). Study it top to bottom.
- **Best architecture reference: AMZ `fsd_skeleton`** (ROS1 but the canonical perception -> estimation -> control layering everyone copies).
- **Best sim to start with: EUFS `eufs_sim` / `eufs_sim2`** (ROS2, Gazebo, rule-compliant tracks) or **FSDS** (Unreal/AirSim based).
- Nearly every serious team: **ROS2 + colcon + ament_cmake, one shared `_msgs` interface package, Docker dev environment, pre-commit with clang-format + black, packages grouped by pipeline stage under `src/`**.
- Most top European teams (AMZ, KA-RaceIng, KTH, Monash) keep their current stack **private** and only publish sensor-driver forks; don't waste time hunting for their core code.

---

## 1. Teams from your spreadsheet

### Quick comparison table

| Team | Org | Driverless? | ROS | Repo strategy | Build system | Notable |
|---|---|---|---|---|---|---|
| Carnegie Mellon Racing | `carnegiemellonracing` | **Yes** (core now private) | ROS2 Humble | DV monorepo (private) + public support repos | colcon/ament (inferred), CMake presets for firmware | Docker compose dev env, Foxglove, CUDA perception |
| AMZ Zurich | `AMZ-Racing` | **Yes** (current stack private) | ROS1 Kinetic (public skeleton) | Monorepo skeleton (`fsd_skeleton`) | catkin | THE canonical FS DV architecture |
| Gaucho Racing (UCSB) | `Gaucho-Racing` | **Yes** (small scale) | ROS2 Humble | Single-workspace repo (`Autonomous`) | colcon | TensorRT YOLO cone detection, pure pursuit, F1TENTH-style |
| HyTech (Georgia Tech) | `hytech-racing` | No (EV, but most modern tooling) | none (Foxglove/MCAP though) | Monorepo (MCUs) + per-domain repos | PlatformIO, CMake + Conan 2, Nix | NixOS on Pi, DBC -> protobuf codegen, MCAP logging |
| UBC Formula Electric | `ubcformulaelectric` | No | none | Monorepo (`Consolidated-Firmware`) | CMake presets (v6) + CPM | JSON CAN schemas + codegen, Tracksight telemetry |
| Waterloo FE | `UWaterloo-Formula-Electric` | No | none | Monorepo (`firmware`) | GNU Make (recursive) | GHCR-prebuilt devcontainer, DBC -> C codegen, MISRA CI, HIL testbed |
| Concordia | `concordia-fsae` | No | none | Monorepo (`firmware`) | **Buck2** + pixi + uv | YAML CAN network defs, pre-commit, drive-stack (Linux services) |
| Queen's | `qfsae` | No | none | Monorepo (`zenith`) | per-project (STM32/Arduino) | Folder-per-project monorepo, wiki + per-folder READMEs |
| Dallas Formula Racing | `DallasFormulaRacing` | No | none | Multi-repo | Docker compose (telemetry) | CAN -> Redis -> Kafka telemetry pipeline, onboarding repo |
| Cyclone Racing (Iowa St) | `CR-Formula` | No | none | Multi-repo (board-per-repo) | STM32/Arduino makefiles | STM32 drivers as git submodule, GH Pages wiki |
| UVic | `UVicFormulaMotorsport` | No | none | Multi-repo (board-per-repo) | STM32 per-repo | CAN test bench culture |
| WSU (actual org: `wazzu-racing`) | `wazzu-racing` | No | none | Multi-repo | embedded per-repo | Telemetry/data-viz culture (Svelte viewer) |
| Auckland WDCC | `UoaWDCC` | No (web dev club) | none | Multi-repo TypeScript | npm | Not motorsport software; skip |
| Manitoba, Columbia, Swinburne | no links | n/a | n/a | n/a | n/a | Nothing to review |

### Detail on the driverless-relevant ones

#### Carnegie Mellon Racing (CMR)

Their actual driverless codebase (`driverless`) went **private** in the last couple of years. What's public tells you a lot anyway:

- **`driverless-docker`**: their dev environment. Docker compose with three services: the main `26x` container built `FROM osrf/ros:humble-desktop-full` (clones the private repo inside using a GitHub PAT passed as a compose secret), an `ml-dev` container (separate ML training environment, optional GPU passthrough via profiles), and a `novnc` container so GUI tools (RViz, rqt_graph) render in the browser at `localhost:8080`. Foxglove bridge exposed on port 8765. Rosbags and a test workspace mounted as volumes.
- **`iSAM2_SLAM`** (C++, GTSAM-based factor-graph SLAM), **`PerceptionsLibrary22a`** (Python perception), **`camera_fusion`**, **`lidar_camera_calibration`**: pipeline components that were split out.
- Forks that reveal the sensor stack: `HesaiLidar_ROS_2.0`, `zed-ros2-wrapper` (ZED stereo), `ros2_numpy`, and TUM's `global_racetrajectory_optimization` for raceline generation.
- Their firmware `monorepo` (separate from driverless) is STM32 ECUs, folder-per-ECU, **CMake with CMakePresets.json**, shared `stm32f413-drivers` library, `cmake/` shared toolchain dir.

Takeaway: ROS2 Humble, docker-compose-first onboarding, browser-based visualization (noVNC + Foxglove), ML training environment isolated from the car stack.

#### AMZ Zurich

The benchmark team. Note the `AMZ-Driverless` org no longer exists; everything is under `AMZ-Racing`. Their current competition code is private; what's public:

- **`fsd_skeleton`** (2019, ROS1 Kinetic, catkin): the architecture template most FS DV teams started from. Layout:

```
fsd_skeleton/
├── fsd_environment.sh        # sources ROS + workspace, loads aliases
├── fsd_aliases               # FSD_build, FSD_launch_<mission>, FSD_rviz_*
├── update_dependencies.sh    # wstool + rosdep bootstrap
└── src/
    ├── 0_fsd_common/
    │   ├── fsd_common_meta/   # top-level mission launch files
    │   └── fsd_common_msgs/   # shared .msg interface package (the contract)
    ├── 1_perception/          # lidar_cone_detector, vision_cone_detector + perception_meta
    ├── 2_estimation/          # slam, velocity_estimator + estimation_meta
    ├── 3_control/             # control_pure_pursuit + control_meta
    ├── 4_continuous_integration/rosdep/   # custom rosdep yaml
    └── fssim_interface/       # bridge to simulator, can be excluded from builds
```

  Key ideas: numbered pipeline layers so data flow reads top to bottom; each layer has a `*_meta` package holding only launch files and config; **one shared msgs package** (`Cone.msg`, `ConeDetections.msg`, `Map.msg`, `CarState.msg`, `ControlCommand.msg`, `Mission.msg`) that every functional package depends on; dummy nodes included so the full graph runs end to end out of the box; mission-oriented launch aliases (acceleration, skidpad, autocross, trackdrive); sim packages blacklistable from the build. Style rules (Google C++, PEP8, `CamelCase.msg`) codified in the README.
- **`fssim`**: their Gazebo-based simulator (ROS1), plugs into the skeleton via `fssim_interface`.
- **`rbb_core`** (Rosbag Bazaar): web platform for cataloging rosbags, with Docker deploy and an OpenAPI-first API. Interesting later for data management.
- Recently active public repos are sensor-driver forks (`HesaiLidar_ROS_2.0`, `fixposition_driver`, `ouster_decoder`) and tools (`random-track-generator`, `fs-trackdraw`, `cim-hil-testing`), which implies a ROS2 lidar + GNSS/INS stack today.
- Their system is documented in the paper "AMZ Driverless: The Full Autonomous Racing System" (arXiv 1905.05150), still the best end-to-end description of an FS driverless architecture.

#### Gaucho Racing (UCSB)

- **`Autonomous`** repo: ROS2 Humble workspace for cone-based navigation on an F1TENTH-style testbed. Single main package `cone_nav` containing mixed C++ and Python nodes. Pipeline: ZED 2i stereo -> TensorRT YOLO cone detector (C++) -> depth back-projection localizer (C++) -> Delaunay triangulation centerline planner (Python) -> pure pursuit controller (C++) -> `AckermannDriveStamped`. Uses standard `vision_msgs`/`ackermann_msgs` rather than custom messages. Small and readable; a good "minimum viable pipeline" reference.
- **`Firmware`** monorepo: STM32, CMake presets v3 + Ninja, folder-per-ECU with a shared `Lib/` and `ProjectTemplate/`, CI workflows for autoformat, autogen, linter, and HOOTL unit tests. The `CMAKE.md` and onboarding docs your spreadsheet praised are here.

#### HyTech Racing (Georgia Tech)

No driverless, but the most modern software practice of any spreadsheet team, and much of it transfers directly:

- **`Monorepo`**: all MCU firmware (ACU, CCU, VCF, VCR, Dashboard) in one **PlatformIO** project.
- **`drivebrain`**: the onboard Linux compute (Raspberry Pi). C++ built with **CMake + Conan 2** (`conanfile.py`, `CMakeUserPresets.json`), cross-compiled in Docker, deployed as a **systemd service on NixOS**. Runs handwritten C++ plus **MATLAB Simulink generated** controllers/estimators, VectorNav INS driver, and an integrated **Foxglove websocket server** for live telemetry and parameter tuning. Data recorded as **MCAP**.
- **`hytech_nixos`**: Nix flake describing the entire Pi OS image (reproducible car computer).
- **`HT_CAN`**: single source of truth for the CAN network. DBC file + Nix-based codegen (`dbc_to_proto`) generating protobuf libraries, published via GitHub releases and a GH Action.

#### The EV-firmware teams (patterns worth stealing even though they're not DV)

- **Waterloo `firmware`**: dev container prebuilt in CI and pushed to GHCR, consumed by tag (`uwfe-dev:stable`); DBC -> C code generation at build time with `cantools` (single `2024CAR.dbc` source of truth); cppcheck + MISRA in CI; Unity/CMock host unit tests per board; Python HIL testbed in-repo; CI auto-publishes built binaries to GitHub Releases.
- **UBC `Consolidated-Firmware`**: CMakePresets v6 with separate firmware/dev/test presets, CPM for CMake dependency fetching, JSON schemas for CAN bus definitions with codegen scripts, `dbc-release.yml` CI, in-repo telemetry web app (Tracksight).
- **Concordia `firmware`**: the boldest build choice: **Buck2** (Meta's build system) over the whole monorepo, with `pixi` (conda-forge) pinning tools like uncrustify and `uv` for Python. YAML CAN network definitions under `network/definition/` (buses/data/discrete values). `drive-stack/` holds Linux-side services (can-bridge, carputer, ota-agent, dashboard), `components/` per-ECU firmware, `embedded/platforms|toolchains`. Heavy pre-commit usage (uncrustify, yamlfmt, taplo, shfmt).
- **Queen's `zenith`**: everything in one repo organized as folder-per-project with per-folder READMEs and a CONTRIBUTING.md; docs live in a wiki. Simple and effective for a small team.
- **Dallas**: multi-repo, but their `onboard-car-software` is a neat containerized telemetry pipeline: CAN deserializer -> Redis -> Kafka connector, DBC files dropped in a folder, `.env`-driven config, docker compose.

---

## 2. Additional FSAE/FSG driverless teams

### Teams with substantial public driverless code

#### QUT Motorsport (Queensland, Australia) — `QUT-Motorsport/QUTMS_Driverless` ⭐ best reference

Active (July 2026), public, competition-proven (second competition-ready autonomous FSAE car in Australasia, completed a full 10-lap Trackdrive in 2024). **This is the closest thing to what you're building.**

- **ROS2 Jazzy**, colcon/ament, single monorepo workspace.
- Layout:

```
QUTMS_Driverless/
├── .clang-format, .pre-commit-config.yaml, pyproject.toml   # black + isort config
├── .github/workflows/pre_commit.yaml
├── docker/
│   ├── Dockerfile.base        # FROM osrf/ros:jazzy-desktop; rosdep install over src/
│   ├── Dockerfile.overlay     # user + workspace layer on top of base
│   ├── docker-compose.yml     # base image + terminal service, host network/ipc/pid
│   ├── cyclonedds.xml         # pinned DDS config
│   └── Makefile               # wraps compose with USERNAME/UID env
├── installation/              # setup docs + install scripts
├── src/
│   ├── common/        # driverless_common, driverless_msgs, rosboard, rviz plugins,
│   │                  #   QUTMS_Embedded_Common (git submodule shared with firmware)
│   ├── perception/    # lidar_pipeline, ground_plane_segmenter, perception_bringup
│   ├── navigation/    # slam_gridmap, planners, vector_pursuit_controller (submodule),
│   │                  #   nav_bringup  (built on ROS2 Nav2!)
│   ├── control/       # controllers, velocity_controller, cmdvel -> ackermann
│   ├── hardware/      # canbus, steering_actuator
│   └── operations/    # vehicle_bringup, telem_bringup, rosbag_creator, vehicle_urdf
└── tools/             # qutms_cli_tools, telemetry_dashboards, topics_to_record
```

- Notable decisions: after years of custom SLAM/planning they **replaced custom navigation with off-the-shelf Nav2** components (documented in arXiv 2311.14276) and wrapped them with FS-specific packages; `*_bringup` packages per group hold launch/config; custom `driverless_msgs` interface package; external reused packages pulled in as **git submodules** rather than vendored; base/overlay docker split so dependency changes don't force full rebuilds; `/dev/shm` mounted and host networking for DDS across containers; a pinned CycloneDDS XML config in the repo.
- They also maintain a **hard fork of `eufs_sim`** updated for modern ROS2, and `qutms_msgs`, `QUTMS_AV_Sim`, MPC experiments (`Spacial-MPC`), `PCL_DBSCAN`.

#### EUFS (Edinburgh) — GitLab `gitlab.com/eufs`

- **`eufs_sim`** / **`eufs_sim2`**: the standard open FS driverless simulator. ROS2, ament_cmake/ament_python (package format 3), Gazebo-based, rule-compliant tracks, random track generation, configurable vehicle models, launcher GUI. `eufs_sim2` is the newer lightweight rewrite.
- **`eufs_msgs`**: a complete, battle-tested message set for an FS DV pipeline (`ConeArray`, `ConeArrayWithCovariance`, `CarState`, `CanState`, `WheelSpeeds`, lap stats, etc). Even if you define your own msgs, copy the vocabulary. C++14, ament linters (`ament_copyright`, `ament_flake8`, `ament_pep257`) wired as test dependencies.
- Their competition AI stack itself is not public.

#### BITFSD (Beijing Institute of Technology) — `bitfsd/fsd_algorithm`

One of the only **complete open pipelines** (perception through control): ROS1, C++/CUDA, includes lidar and camera cone detection, SLAM, planning, control. Last touched 2022 so treat it as a study artifact like `fsd_skeleton`, not a base.

#### MIT Driverless — `cv-core/MIT-Driverless-CV-TrainingInfra`

Perception/training focused: CVC-YOLOv3 cone detection and **RektNet** keypoint network, PyTorch, plus their paper "Accurate Low Latency Visual Perception for Autonomous Racing" (arXiv 2007.13971). Good for the perception/ML subteam; no full-stack repo.

#### FaSTTUBe (TU Berlin) — via `papalotis/ft-fsd-path-planning`

Their path planning is public, **active (2026)**, pure Python, and deliberately portable: colorblind (works without cone color), sorts cones, computes the centerline, no ROS dependency so you can wrap it in a ROS2 node directly. One of the most practically reusable single components out there.

#### BCN eMotorsport (UPC Barcelona) — via member repos

Team org is private but members publish real components: `origovi/urinay` (Delaunay-based colorblind centerline + track limits, C++, ROS, updated 2025), `origovi/CCAT` (cone classification and tracking), `fetty31/tailored_mpc` (curvature NMPC used at FSG/FSS), `fetty31/cruise_control`. Strong planning/control references.

#### Chalmers FS Driverless

- Old org `chalmersfsd` (2019, abandoned): interesting as the counterexample. **No ROS**: a microservices architecture on **OpenDLV/libcluon**, one repo per microservice (`cfsd-perception-detectcone`, `cfsd-logic-pathplanner`, `cfsd-proxy-cangw-lynx`, ...), Docker per service. Shows what multi-repo microservices looks like; most teams found monorepo + ROS easier to sustain.
- New org `Chalmers-Formula-Student`: publishes **`coneScenes`** (active 2026), a LiDAR dataset with 3D annotated cones, plus `fakeScenes` synthetic lidar generator. Core stack private.

#### Unicamp E-Racing (Brazil) — `Unicamp-E-Racing/driverless-2019`

Full 2019 pipeline (Python), historical reference.

#### Formula Student Technion — `FSTDriverless/FSTImplementation`

2019 Python implementation with an AirSim-based simulation heritage (their AirSim fork seeded what became FSDS).

### Teams that are known DV competitors but keep code private (don't hunt)

| Team | What IS public | Signal |
|---|---|---|
| KA-RaceIng (Karlsruhe) | `ROS2-Docker` (active 2026), forks of g2o, hpipm, blasfeo, osqp-eigen, Hesai ROS2 driver | ROS2 + graph SLAM + QP-based MPC, docker-per-domain images |
| KTH FS (Sweden) | Forks: direct_lidar_inertial_odometry (active 2026), fssim, Ouster/SBG/Basler/ZED drivers | ROS, DLIO-based odometry; core private |
| Monash Motorsport | `YOLOs-CPP-TensorRT` (header-only TensorRT YOLO, active 2026), livox_ros_driver2 fork, MoTeC pre-commit workflows | TensorRT camera perception + Livox lidar; core private |
| municHMotorsport | Nothing relevant (org dormant since 2016) | n/a |
| StarkStrom Augsburg | Org not on GitHub anymore; member published `fsd_racetrack_dataset` | n/a |
| UGRacing (Glasgow) | Only old datalogger firmware | n/a |
| Elbflorace (Dresden) | `OpenSourceVCU` only | n/a |
| E-Agle TRT (Trento) | Extensive EV firmware, telemetry (MQTT, Influx), CAN flashing tools; no DV code public | Good telemetry patterns |

---

## 3. Community resources you can use directly

| Resource | What it is | Status |
|---|---|---|
| `FS-Driverless/Formula-Student-Driverless-Simulator` (FSDS) | AirSim/Unreal-based FS sim, ROS1 + ROS2 bridges, used for FSOnline | maintained |
| `eufs_sim` / `eufs_sim2` (GitLab) | ROS2 Gazebo sim, rule-compliant tracks, launcher | active; QUT maintains a modernized hard fork |
| `PacSim/pacsim` | Newer lightweight FS driverless simulator (C++) | active 2026 |
| FSOCO dataset (`ddavid/fsoco`) | Community cone image dataset (segmentation/detection labels) | standard for camera training |
| `Chalmers-Formula-Student/coneScenes` | LiDAR dataset, 3D annotated cones | active 2026 |
| `papalotis/ft-fsd-path-planning` | Portable colorblind path planning (Python) | active 2026 |
| `papalotis/drawing-to-fsd-layout`, `layout-merchant`, AMZ/`random-track-generator`, `mvanlobensels/random-track-generator` | Track layout generation/collection tools | active |
| TUM `global_racetrajectory_optimization` | Raceline optimization (min curvature / min time) | widely forked (CMR forks it) |
| `eufs_msgs` | Ready-made FS DV message definitions | active |

---

## 4. Common patterns across driverless teams

**Repo and workspace structure**
1. **Monorepo = one colcon workspace** is the dominant model for the autonomous stack (AMZ skeleton, QUT, CMU, Gaucho, BITFSD). The repo root contains `src/` and tooling; `build/`, `install/`, `log/` are gitignored.
2. **Packages grouped by pipeline stage** under `src/`: perception, estimation/SLAM (or "navigation"), planning, control, plus `common/`, `hardware/` (CAN, actuators), and `operations/` or `*_meta` (launch and bringup). AMZ numbers the layers (`0_common`, `1_perception`, ...); QUT uses named groups. Same idea.
3. **One shared interface (`*_msgs`) package** that defines the contract between stages (`Cone`, `ConeArray(WithCovariance)`, `CarState`, `ControlCommand`, mission/state msgs). Everything depends on it; nothing in it depends on anything else. Universal pattern (AMZ `fsd_common_msgs`, EUFS `eufs_msgs`, QUT `driverless_msgs`, `qutms_msgs`).
4. **Bringup/meta packages** contain only launch files, params, RViz/Foxglove configs; functional packages stay launch-light. Mission-oriented top-level launches (acceleration, skidpad, autocross, trackdrive, inspection/EBS test).
5. **External reused packages** come in as git submodules (QUT) or vcstool `.repos` files (ROS1 era used wstool/rosinstall); vendored forks only when patches are needed (everyone forks their lidar vendor driver: Hesai, Ouster, Livox, ZED).
6. **Sim integration is a thin interface package** (`fssim_interface`, QUT's sim bringup) that can be excluded from car builds.
7. Embedded firmware and the autonomous stack live in **separate repos** at nearly every team (CMU, QUT, Gaucho, AMZ); shared CAN definitions bridge them (QUT shares `QUTMS_Embedded_Common` as a submodule into both).

**Build and dependencies**
8. **ROS2 + colcon + ament_cmake/ament_python, package format 3** is the standard for anything started after ~2021. Distros observed: Humble (CMU, Gaucho), Jazzy (QUT). ROS1/catkin only in legacy artifacts.
9. **rosdep is the dependency mechanism**: CI/Docker runs `rosdep install --from-paths src --ignore-src`. Teams with exotic deps add a custom rosdep yaml (AMZ).
10. C++14/17 with `-Wall -Wextra -Wpedantic`; Python via the ament_python build type; CUDA/TensorRT isolated inside the perception packages that need it.

**Dev environment**
11. **Docker-first onboarding, everywhere.** The winning shape is QUT's: a `base` image (`FROM osrf/ros:<distro>-desktop`) that installs rosdeps, and an `overlay` image adding the user + workspace, orchestrated by docker-compose + Makefile. CMU adds noVNC for browser GUI and a separate ML training container. Waterloo/HyTech prebuild the image in CI and pull by tag instead of building locally.
12. **DDS config is pinned in-repo** (QUT's `cyclonedds.xml`), containers run with host network + IPC and `/dev/shm` mounted so ROS2 discovery works across containers.
13. GPU access via compose profiles / nvidia container toolkit for training; TensorRT engines built on-device for inference.

**Quality and CI**
14. **pre-commit is the universal lint harness**: clang-format (C++), black + isort (Python), plus whitespace fixers; CI just runs `pre-commit run --all-files` (QUT's only workflow). Firmware teams add MISRA/cppcheck (Waterloo) or uncrustify (Concordia).
15. CI builds the workspace in the same Docker image developers use. EUFS wires ament linters as package `test_depend`s.
16. Style guides codified in the repo (AMZ README: Google C++ style, PEP8, ROS naming, `CamelCase.msg`).

**Data and telemetry**
17. **Foxglove has replaced RViz-only workflows** for live telemetry and log review (CMU port 8765, HyTech integrated websocket server + Foxglove parameter tuning). **MCAP** is the emerging log format (HyTech, QUT rosbag tooling with curated `topics_to_record`).
18. **Single source of truth for CAN**, with codegen: DBC or YAML/JSON definitions generating C structs (Waterloo, UBC), protobuf (HyTech), or ROS msg bridges. The DV stack talks to the car through a `canbus`/`can-bridge` package.
19. Rosbag discipline: dedicated recorder package with a curated topic list, bags stored outside the repo, mounted into containers.

**Strategy-level patterns**
20. **"Don't rewrite what exists": the strongest recent trend.** QUT replaced years of custom SLAM/planning/control with tuned **Nav2** components and got their best-ever competition result. FaSTTUBe/BCN publish reusable planning components precisely because these problems are commodity now. Custom work concentrates in perception (cone detection) and vehicle-specific control/safety.
21. Successful teams publish datasets and tools (Chalmers coneScenes, FSOCO) but keep competition integration private.

---

## 5. Reference monorepo structure

A synthesis of QUT (primary), AMZ (layering), and CMU (dev env), adapted for a new ROS2 team. This is a starting point, not a prescription.

```
umsae-driverless/                      # one repo = one colcon workspace
├── README.md                          # what/why, quickstart, links to docs/
├── LICENSE
├── .gitignore                         # build/ install/ log/ bags/ *.engine ...
├── .gitmodules                        # external ROS packages as submodules
├── .clang-format                      # C++ style (pick one, never argue again)
├── .pre-commit-config.yaml            # clang-format, black, isort, whitespace
├── pyproject.toml                     # black/isort/ruff config
├── dependencies.repos                 # optional: vcstool alternative to submodules
│
├── .github/
│   └── workflows/
│       ├── pre_commit.yaml            # lint on every PR
│       ├── build.yaml                 # colcon build + colcon test in the dev image
│       └── image.yaml                 # build+push dev image to GHCR on main
│
├── docker/
│   ├── Dockerfile.base                # FROM osrf/ros:jazzy-desktop, rosdep install
│   ├── Dockerfile.overlay             # user setup + workspace, dev tools
│   ├── docker-compose.yml             # dev, sim, (optional) ml profiles
│   ├── cyclonedds.xml                 # pinned DDS config
│   └── Makefile                       # make dev / make sim / make build
│
├── docs/
│   ├── onboarding.md                  # zero-to-running-sim guide (test on a fresh laptop)
│   ├── architecture.md                # pipeline diagram, topic map, frames/TF tree
│   └── conventions.md                 # naming, style, branch/PR rules
│
├── src/
│   ├── common/
│   │   ├── umsae_msgs/                # THE interface package: Cone, ConeArrayWithCovariance,
│   │   │                              #   CarState, ControlCommand, Mission, ...
│   │   │                              #   (start by copying eufs_msgs vocabulary)
│   │   └── umsae_common/              # shared utils, params, py/cpp helpers
│   │
│   ├── perception/
│   │   ├── lidar_pipeline/            # ground removal, clustering, cone candidates
│   │   ├── camera_pipeline/           # YOLO(TensorRT) cone detection + depth assoc
│   │   └── perception_bringup/        # launch + params only
│   │
│   ├── estimation/                    # (QUT folds this into "navigation")
│   │   ├── state_estimation/          # wheel odom + IMU + GNSS fusion (try robot_localization first)
│   │   ├── slam/                      # cone map + localization (try Nav2/existing SLAM first)
│   │   └── estimation_bringup/
│   │
│   ├── planning/
│   │   ├── path_planner/              # centerline from cones (Delaunay; see ft-fsd-path-planning)
│   │   └── planning_bringup/
│   │
│   ├── control/
│   │   ├── controllers/               # pure pursuit first, MPC later
│   │   └── control_bringup/
│   │
│   ├── hardware/
│   │   ├── canbus/                    # CAN <-> ROS bridge, generated from the team DBC
│   │   ├── sensors/                   # vendor driver configs/wrappers (drivers themselves = submodules)
│   │   └── actuation/                 # steering/brake/throttle interfaces, EBS state machine
│   │
│   ├── operations/
│   │   ├── vehicle_bringup/           # mission launches: acceleration, skidpad,
│   │   │                              #   autocross, trackdrive, inspection
│   │   ├── vehicle_urdf/              # robot description + TF
│   │   └── recording/                 # rosbag recorder + topics_to_record.yaml
│   │
│   └── sim/
│       └── sim_interface/             # adapter to eufs_sim/FSDS; excluded from car builds
│
└── tools/                             # non-ROS: CLI helpers, dataset scripts,
                                       #   Foxglove layouts, track generators
```

Companion repos (separate from this monorepo, following universal practice):
- `umsae-firmware` (already exists in some form): the DBC/CAN definition should live in exactly one place and be consumed by both repos (submodule or codegen artifact, like QUT's `QUTMS_Embedded_Common` or HyTech's `HT_CAN` releases).
- Optionally an `ml-training` repo/container later (CMU pattern) so heavy training deps never pollute the car stack.

---

## 6. Recommendations

Common-pattern recommendations (what the field converged on; low-risk defaults):

1. **ROS2 on an LTS distro (Humble now, Jazzy if your compute runs Ubuntu 24.04) + colcon + ament.** No team starting today picks anything else.
2. **One monorepo = one workspace**, packages grouped by pipeline stage, with a single `umsae_msgs` interface package. Copy `eufs_msgs` vocabulary as your starting point.
3. **Docker base/overlay dev environment from day one** (QUT's `docker/` directory is copy-adaptable), with the image prebuilt in CI and pushed to GHCR (Waterloo pattern) so onboarding is "install docker, run make dev".
4. **pre-commit with clang-format + black + isort**, enforced by a single CI workflow. Add `colcon build`/`colcon test` CI once packages exist.
5. **Don't build SLAM/planning/control from scratch.** Evaluate Nav2 (QUT proved it works for FS), `robot_localization`, `ft-fsd-path-planning`, and pure pursuit before writing anything custom. Spend your custom-engineering budget on perception and the vehicle/safety interface, the parts nobody else can do for you.
6. **Start in simulation**: eufs_sim2 or QUT's eufs_sim fork (Gazebo, lighter) or FSDS (prettier, heavier). Keep the sim adapter behind a thin `sim_interface` package.
7. **Single source of truth for CAN** shared with the firmware team, with codegen into the `canbus` package.
8. **Foxglove + MCAP** for telemetry and log review; curated topic list for recording.
9. Study order for the team: QUTMS_Driverless (structure and tooling) -> AMZ fsd_skeleton + paper (architecture concepts) -> eufs_sim/msgs (sim + interfaces) -> ft-fsd-path-planning and urinay (planning) -> FSOCO/coneScenes (perception data).

Design decisions that are genuinely yours to make (options observed, no consensus):

- **DDS/RMW choice**: CycloneDDS (QUT pins it) vs FastDDS (ROS2 default). Teams pin one and ship the config; which one is your call after testing on your network.
- **Submodules vs vcstool `.repos`** for external packages: QUT uses submodules; ROS ecosystem convention is `.repos`. Either works; pick one and document it.
- **Perception primary sensor**: lidar-first (QUT, KTH, Chalmers dataset), camera-first (MIT, Monash TensorRT YOLO), or both fused (AMZ, CMU). Drives your budget and package layout more than any other choice.
- **Nav2-wrapped stack vs bespoke pipeline**: QUT's Nav2 result is compelling for a new team, but top European teams still run bespoke estimators/MPC. Bespoke pays off only once you have people to maintain it.
- **Custom msgs vs standard msgs**: Gaucho got away with `vision_msgs` + `ackermann_msgs` only; most teams define custom cone/state msgs. Custom is more expressive, standard is more interoperable with off-the-shelf tools.
- **Where estimation lives**: its own layer (AMZ) vs folded into navigation (QUT). Cosmetic, but decide before the folder structure ossifies.
- **Build ambition**: plain colcon is the norm; Concordia shows Buck2 and HyTech shows Nix/Conan are viable if you have the appetite. For a first-year DV team, plain colcon is the defensible default.

---

## Appendix: research caveats

- CMU, AMZ, KA-RaceIng, KTH, Monash, Chalmers, BCN keep current competition code private; their entries above are reconstructed from public support repos, forks, docs, and papers.
- The `AMZ-Driverless` GitHub org no longer exists (repos moved to `AMZ-Racing`); the WSU org in the spreadsheet is actually `wazzu-racing`.
- UVic, WSU, CR-Formula, UoaWDCC, and Dallas were assessed from org listings and READMEs rather than full clones, since they have no driverless-relevant code.
- Snapshot date: July 12, 2026. Activity claims ("active") mean commits within the last ~6 months.

---

## Council Review

Second-pass review of the recommended tech stack (Section 6), produced July 12, 2026 by an LLM council: five independent advisors (Contrarian, First Principles, Expansionist, Outsider, Executor) each critiqued the stack, anonymously peer-reviewed each other, and a chairman synthesized the verdict. Everything above this header is the first pass; everything below is the second.

### Where the council agrees

- **The technical choices themselves are sound.** No advisor disputed ROS2 + colcon, one monorepo, a single msgs package, reuse-over-rewrite (Nav2, robot_localization, ft-fsd-path-planning, pure pursuit), sim-first, or Foxglove + MCAP. The stack correctly mirrors what the field converged on.
- **The risk is sequencing, not selection.** Four of five advisors independently made the same point: this stack solves a mature team's problems (scale, reproducibility, multi-contributor hygiene) while a founding team's actual failure mode is losing three ROS-newcomers to environment friction and attrition before anything drives. Beginners quit on environment problems, not algorithm problems.
- **Three items are cheap now and expensive to retrofit; do them on day one:** the single colcon workspace with the msgs package, pre-commit with clang-format + black, and Foxglove + MCAP. Everything else can wait for the pain it solves to actually exist.
- **Three items are premature as "day one" requirements:** CI-prebuilt Docker images pushed to GHCR (a plain Dockerfile plus a devcontainer README is enough until there are ~5 contributors), CAN codegen shared with a firmware integration that does not exist yet (stub the interface, define nothing), and the Buck2/Nix "build ambition" bullet (delete it; no student team of this size will maintain either).
- **The doc's biggest gap is people, not tools.** Knowledge continuity across graduation, a bus factor of one (the founder), and a documented onboarding path are the actual multi-year risks, and Section 6 says nothing about them. The stack should be graded on one axis: does a new recruit get from clone to a moving sim car with a node publishing to Foxglove in their first week.

### Where the council clashes

- **Humble vs Jazzy.** The Executor argued to pin Humble: two more years of tutorials, Stack Overflow answers, and copy-pasteable code is a real subsidy for beginners. The Contrarian countered that the deferral is fake anyway: the one live reference stack (QUTMS) runs Jazzy, so following it means Jazzy has effectively been chosen without admitting it. Resolution: this is a real decision, not a deferral. Make it explicitly, and record why.
- **Scaffold-as-curriculum vs scaffold-as-friction.** The Expansionist argued the Docker/CI/pre-commit scaffolding IS the recruiting and succession plan: one clone, one command, sim running in an hour, which is how a founder-dependent project becomes a program. The other four called that same scaffolding the attrition risk. Peer review sided heavily with the majority for year one, but the Expansionist's framing becomes correct the moment there are more than a handful of contributors. The disagreement is about when, not whether.
- **Sim-first vs hardware-first.** The doc says start in simulation; the Contrarian called sim-first with no fixed compute or sensors the classic FS trap (a beautiful pipeline against eufs physics that dies on real latency, calibration, and a Jetson), made worse by Winnipeg winters already shrinking the reality feedback loop. The Expansionist argued the opposite: forced sim maturity is the team's structural advantage. Resolution below.

### Blind spots the council caught (things no single advisor or the doc itself covered)

- **Money and governance are upstream of everything here.** No advisor initially engaged with budget, and the doc never does: a Jetson, a camera or lidar, cones, and CAN hardware cost real dollars a not-yet-sanctioned subteam may not have. How the DV subteam gets UMSAE buy-in, shares a vehicle platform, and funds a sensor decides "lidar vs camera vs fusion" long before any architecture doc does. The "deferred" sensor decision is not a decision; it is a placeholder for an unfunded constraint.
- **Nav2's fit deserves validation, not just citation.** Nav2 was designed for slow 2D indoor navigation. QUT proved a wrapped version works for FS, but the council flagged that adopting it on citation alone, without checking it against target speeds and the FS rulebook, is the one technical reuse claim in Section 6 that went unexamined.
- **Compute target selection silently decides other "deferred" items.** Picking Jetson vs x86 early determines whether sim work transfers, which sensor drivers matter, and how perception is built. It belongs on the decide-early list, not the deferred list.

### The recommendation

Adopt the stack as written but split Section 6 into two phases instead of one list. **Phase 0 (now):** repo + workspace + `umsae_msgs` + pre-commit + Foxglove/MCAP + eufs_sim running, a plain Dockerfile, and a written 30-minute onboarding guide tested on a fresh laptop. Explicitly pick the ROS2 distro and record the reasoning. **Phase 1 (triggered by contributor count, not the calendar):** GHCR-prebuilt images and build CI at roughly 5 contributors, CAN codegen when a firmware counterpart actually exists, MPC and bespoke anything only when there are people to maintain them. Delete Buck2/Nix from consideration. Add two missing workstreams the doc omits entirely: a funding/hardware plan (cheap camera + small compute this fall, before snow, so perception meets reality at least once in year one) and a continuity plan (decision log, onboarding doc, at least two people who can build and run the stack).

### The one thing to do first

Before any more architecture work: get eufs_sim running with one node publishing to one topic, visible in Foxglove, and write down the exact steps as the onboarding guide. If a new recruit cannot reproduce it in under an hour, fix the guide before touching the stack. That single artifact tests the dev environment, the sim choice, the telemetry choice, and the onboarding thesis all at once.

*Process note: peer review ranked the Contrarian's critique strongest (4 of 5 reviewers) and unanimously flagged the Expansionist as the biggest blind spot, while crediting its succession-plan framing as the right lens for later phases.*
