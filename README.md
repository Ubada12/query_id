# Dataset Documentation

## 1. Dataset Overview

This dataset is built for training a **YOLO-based single-class object detector** to detect **goats in a farm chute** using CCTV cameras.

The dataset contains both **positive and negative samples** across multiple camera views, orientations, lighting conditions, and environmental variations. It is intentionally designed to reduce **false positives and hallucinations** in real-world, continuous CCTV deployment rather than focusing only on benchmark performance.

---

## 2. Filename Convention

All images follow a single, consistent naming format:

```
<SPLIT>_<LABEL>_<DS>_<TYPE>_<SUBTYPE>_<SEQ>.jpg
```

### Field Definitions

| Field   | Description                                      |
| ------- | ------------------------------------------------ |
| SPLIT   | Dataset split identifier (training / validation) |
| LABEL   | Presence or absence of goat in the frame         |
| DS      | Dataset version                                  |
| TYPE    | Camera or view type                              |
| SUBTYPE | Scene or condition subtype                       |
| SEQ     | Zero-padded sequential number                    |

---

## 3. SPLIT Definitions

| Code | Meaning          |
| ---- | ---------------- |
| tr   | Training split   |
| va   | Validation split |

---

## 4. LABEL Definitions

| Code | Meaning                                           |
| ---- | ------------------------------------------------- |
| pos  | Goat present (at least one goat visible in frame) |
| neg  | No goat present                                   |

---

## 5. Dataset Versions (DS)

| Code | Meaning                                                                        |
| ---- | ------------------------------------------------------------------------------ |
| v1   | Initial dataset with earlier camera setups and limited views                   |
| v2   | Extended dataset with additional views, orientations, and hard-negative mining |

Future versions (v3, v4, …) can be added without breaking compatibility.

---

## 6. TYPE Definitions (Camera / View Types)

| TYPE | Description                                                                                      |
| ---- | ------------------------------------------------------------------------------------------------ |
| t1   | Ceiling-mounted camera (~45° angle), full farm visible, ROI cropped to chute area                |
| t2   | Top-down vertical view (90°), chute only, short entry–exit distance                              |
| t3   | Top-down camera rotated horizontally; goats move left ↔ right, extended chute using bamboo sides |
| t4   | Same as t3 but with complex backgrounds: sunrise, evening, night lighting, shadows, clutter      |

These TYPE definitions apply to **both positive and negative images**.

---

## 7. SUBTYPE Definitions (Scene / Condition Types)

### Core Subtypes

| SUBTYPE | Meaning                                                       |
| ------- | ------------------------------------------------------------- |
| nrm     | Normal conditions                                             |
| emp     | Empty chute (no goats) with humans passing normal events      |
| hdn     | Hard negatives (humans, other animals, ambiguous clutter)     |
| brk     | Broken or unstable camera (shake, occlusion, mounting issues) |
| ngt     | Night or low-light conditions                                 |
| rot     | Temporary camera rotation                                     |
| shd     | Strong shadows                                                |
| clt     | Heavy clutter, garbage, goat hair, bamboo shadows             |

---

## 8. Mapping to Special Types

The following table maps internally used **Special Types** to standardized SUBTYPE codes.

 Special Type           | Maps to SUBTYPE | Time of Day              | Description                                                                                                                |
| ---------------------- | --------------- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| Special 1              | nrm             | Afternoon                | Normal afternoon conditions, humans passing                                                                                |
| Special 2              | shd             | Border Afternoon–Evening | Sharp sunlight with strong shadows                                                                                         |
| Special 3              | clt             | Evening                  | Heavy clutter, garbage, bamboo shadows                                                                                     |
| Special 4              | clt             | Evening (Late)           | Similar to Special 3, later evening conditions                                                                             |
| Special 5              | rot             | Night (Early)            | Camera temporarily rotated, artificial lights begin                                                                        |
| Special 6              | hdn             | Border Afternoon–Evening | Other animals, humans, ambiguous objects                                                                                   |
| Special 7              | brk             | Afternoon                | Shaky camera, mounting issues, hand occlusion                                                                              |
| Special 8              | ngt             | Night                    | Night-time with artificial lighting                                                                                        |
| Unresolved (neg → sp6) | hdn             | Mixed (Day–Night)        | Ambiguous negative samples extracted from mixed pools; may contain humans, animals, clutter, or partial goat-like patterns |
| Unresolved (pos → sp1) | nrm             | Mixed (Day–Night)        | Valid positive goat samples with mixed lighting and background conditions; exact scene subtype not explicitly separated    |

This mapping ensures consistency while preserving historical annotations. 

### Unresolved Samples

Some samples are marked as **unresolved** due to mixed acquisition sources or lack of deterministic separation during collection.

* **Unresolved negatives** are conservatively treated as **hard negatives (`hdn`)** and are explicitly flagged in metadata notes for future refinement.
* **Unresolved positives** represent valid goat detections under mixed lighting and background conditions and are intentionally kept unsplit.

These samples are clearly marked in the `notes` column to enable targeted review, reclassification, or renaming in future dataset iterations.

---

## 9. Labeling Rules (YOLO Format)

### Positive Images

* Must have a corresponding `.txt` file
* Bounding boxes follow standard YOLO format

### Negative Images

* Either:

  * An empty `.txt` file, or
  * No `.txt` file at all (depending on training pipeline configuration)

No bounding boxes should exist for negative samples.

---

## 10. Design Philosophy

This dataset intentionally prioritizes **camera-matched negatives**, **hard negatives**, and **environmental diversity** over generic object images.

The primary goal is to **minimize false positives and hallucinations** during long-running CCTV deployments rather than solely maximizing benchmark mAP scores.

This design choice ensures robustness, stability, and real-world reliability.
