# Hook Sinskey Data-Risk Note

## Acquisition/class confounding

The inherited filenames expose a perfect association between acquisition group and class across every existing split:

| Split | Defective (`6-4`) | Healthy (`6-3`) |
|---|---:|---:|
| Train | 135 | 46 |
| Validation | 26 | 9 |
| Test | 18 | 6 |

No defective `6-3` image and no healthy `6-4` image exists in the candidate dataset. Background, lighting, positioning, camera settings, tray surface, or acquisition-date cues may therefore predict the class independently of the instrument defect.

Consequences:

- Historical YOLO metrics may overstate defect generalization.
- A random image-level split does not remove this confound because both acquisition groups occur in every split with the same class association.
- Segmentation supervision may reduce but cannot eliminate shortcut learning.
- The controlled benchmark must report this limitation prominently.

Recommended follow-up after the pilot gate:

- Acquire healthy and defective Hook Sinskey examples within the same capture sessions and backgrounds.
- Group future splits by physical instrument and acquisition session.
- Track provenance fields that identify instrument, session, operator, camera, and background.
- Treat current test results as internal-dataset performance, not deployment evidence.
