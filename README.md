# 📄 Dataset Documentation — Goat Detection (YOLO, Single Class)

## 1. Dataset Overview

This dataset is built for training a **YOLO-based single-class object detector** to detect **goats in a farm chute** using CCTV camera feeds.

The dataset contains both **positive (goat present)** and **negative (no goat present)** samples collected across:

* Multiple camera mountings and orientations
* Different chute layouts and structural materials
* Varying lighting conditions (day, evening, night, artificial light)
* Real farm activity (humans, animals, clutter, motion, camera shake)

The dataset is intentionally designed to **minimize false positives and hallucinations** in continuous, real-world CCTV deployments, rather than only optimizing benchmark mAP scores.

---

## 2. End-to-End Dataset Pipeline (Phase 0 → Phase 3)

This dataset was constructed using a strict **multi-phase pipeline** to ensure correctness, reproducibility, and robustness.

### Phase 0 — Raw Collection

* Frames extracted from real CCTV footage
* Multiple camera views, rotations, and environmental conditions
* No assumptions about cleanliness or balance

### Phase 1 — Dataset Staging

Raw data grouped into staging folders by:

* Dataset version (`v1`, `v2`)
* Positive / Negative samples
* Camera type (`t1–t4`)
* Scene subtype (`nrm`, `hdn`, `clt`, etc.)

No renaming is performed at this stage; the focus is **logical grouping only**.

### Phase 2 — Metadata Generation

A metadata **CSV** is generated from the staging structure.

Each row represents **one image–label pair**.

Metadata fields include:

* Split, label, dataset version
* Camera type, scene subtype
* Time-of-day, lighting conditions
* Notes (including unresolved flags)

### Phase 2.5 — Dataset Gatekeeper Validation

A production-grade validation pass enforces:

* No corrupted images
* Exact image–label pairing
* Correct YOLO label format
* Strict positive / negative semantics
* Single-class enforcement (`class_id = 0`)
* No train / validation leakage
* Verified counts and proportions

❗ **Training is blocked if Phase 2.5 fails**

### Phase 3 — Final YOLO Dataset Export (Locked)

* Dataset flattened into YOLO-readable structure
* Explicit `train.txt` and `val.txt` generated
* Final `data.yaml` defines the dataset contract

From this point onward, the dataset is **immutable**.

---

## 3. Final YOLO Dataset Structure

```
dataset_yolo_final/
├── images/
│   ├── train/
│   │   └── *.jpg
│   └── val/
│       └── *.jpg
│
├── labels/
│   ├── train/
│   │   └── *.txt
│   └── val/
│       └── *.txt
│
├── train.txt
├── val.txt
├── data.yaml
└── README.md
```

YOLO only reads:

* `data.yaml`
* `train.txt`
* `val.txt`

Labels are resolved automatically by YOLO via path substitution:

```
images/.../X.jpg → labels/.../X.txt
```

---

## 4. Filename Convention

All images follow a single, consistent naming format:

```
<SPLIT>_<LABEL>_<DS>_<TYPE>_<SUBTYPE>_<SEQ>.jpg
```

### Field Definitions

| Field   | Description                                        |
| ------- | -------------------------------------------------- |
| SPLIT   | Dataset split (`tr` = training, `va` = validation) |
| LABEL   | `pos` (goat present) or `neg` (no goat)            |
| DS      | Dataset version (`v1`, `v2`, …)                    |
| TYPE    | Camera / view type                                 |
| SUBTYPE | Scene or condition subtype                         |
| SEQ     | Zero-padded sequential identifier (`%06d`)         |

This naming is **semantic for humans** but ignored by YOLO during training.

---

## 5. SPLIT Definitions

| Code | Meaning          |
| ---- | ---------------- |
| tr   | Training split   |
| va   | Validation split |

Train / validation split is approximately **70 / 30**, with matched positive–negative ratios.

---

## 6. LABEL Definitions

| Code | Meaning                                |
| ---- | -------------------------------------- |
| pos  | At least one goat visible in the frame |
| neg  | No goat present                        |

---

## 7. Dataset Versions (DS)

| Code | Description                                                             |
| ---- | ----------------------------------------------------------------------- |
| v1   | Initial dataset with earlier camera setups and limited viewpoints       |
| v2   | Expanded dataset with new views, orientations, and hard-negative mining |

Future versions (`v3`, `v4`, …) can be added without breaking compatibility.

---

## 8. TYPE Definitions (Camera / View Types)

| TYPE | Description                                                                                     |
| ---- | ----------------------------------------------------------------------------------------------- |
| t1   | Ceiling-mounted camera (~45°), full farm visible, ROI cropped to chute                          |
| t2   | Top-down vertical view (90°), chute only, short entry–exit distance                             |
| t3   | Top-down camera rotated horizontally; goats move left ↔ right, extended chute with bamboo sides |
| t4   | Same as `t3` with complex backgrounds: sunrise, evening, night lighting, shadows, heavy clutter |

TYPE applies to **both positive and negative samples**.

---

## 9. SUBTYPE Definitions (Scene / Condition Types)

| SUBTYPE | Description                                              |
| ------- | -------------------------------------------------------- |
| nrm     | Normal conditions                                        |
| emp     | Empty chute, no goats                                    |
| hdn     | Hard negatives (humans, other animals, ambiguous shapes) |
| brk     | Camera shake, mounting issues, hand occlusion            |
| ngt     | Night or low-light scenes with artificial lighting       |
| rot     | Temporary camera rotation                                |
| shd     | Strong sunlight and shadows                              |
| clt     | Heavy clutter: garbage, goat hair, bamboo shadows        |

---

## 10. Mapping to Historical Special Types

| Special Type     | SUBTYPE | Time of Day              | Description                                                                    |
| ---------------- | ------- | ------------------------ | ------------------------------------------------------------------------------ |
| Special 1        | nrm     | Afternoon                | Normal afternoon conditions, humans passing                                    |
| Special 2        | shd     | Border Afternoon–Evening | Sharp sunlight with strong shadows                                             |
| Special 3        | clt     | Evening                  | Heavy clutter, garbage, bamboo shadows                                         |
| Special 4        | clt     | Late Evening             | Similar to Special 3 with reduced lighting                                     |
| Special 5        | rot     | Early Night              | Camera temporarily rotated, artificial lights begin                            |
| Special 6        | hdn     | Border Afternoon–Evening | Humans, animals, ambiguous objects                                             |
| Special 7        | brk     | Afternoon                | Shaky camera, mounting issues, hand occlusion                                  |
| Special 8        | ngt     | Night                    | Night-time with artificial lighting                                            |
| Unresolved (neg) | hdn     | Mixed                    | Ambiguous negatives from mixed pools, conservatively treated as hard negatives |
| Unresolved (pos) | nrm     | Mixed                    | Valid goat positives with mixed lighting and background conditions             |

Unresolved samples are explicitly preserved and flagged for future refinement.

---

## 11. Labeling Rules (YOLO Format)

### Positive Images

* Must have a corresponding `.txt` file
* Each line follows:

```
class_id x_center y_center width height
```

* Single-class only (`class_id = 0`)

### Negative Images

* `.txt` file **must exist** and be completely empty
* No whitespace, no bounding boxes

---

## 12. Dataset Statistics (Final)

* **Total images:** 23,976
* **Total positives:** 17,981
* **Total negatives:** 5,996

**Split distribution:**

* Train ≈ 70%
* Validation ≈ 30%

**Positive : Negative ≈ 3 : 1**

---

## 13. Design Philosophy

This dataset intentionally prioritizes:

* Camera-matched negatives
* Hard negatives
* Environmental realism
* Viewpoint diversity

Over generic object images.

The primary goal is **robust real-world performance** with minimal hallucinations during long-running CCTV inference, not merely high benchmark scores.
