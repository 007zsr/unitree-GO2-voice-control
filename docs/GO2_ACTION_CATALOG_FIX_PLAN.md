# Go2 Action Catalog Fix Plan

No safety-release change is made by this report. The fixes below are recommendations only.

## 1. Immediate Code/Mapping Fixes

- Add explicit Go2Adapter handling for `AutoRecoveryGet` before using it on a real robot, because Python SDK returns `(code, data)` and the generic adapter path currently treats that tuple as failure.
- Consider downgrading `auto_recovery_get` from real-robot candidate status to a caution/read-only review item until the adapter has explicit tuple handling.
- Keep Python-side names `AutoRecoverySet/Get` for the project because that is what the installed Python SDK exposes. Document that C++ headers use `AutoRecoverSet/Get` for the same API IDs.
- Keep `walk_upright` and `cross_step` stricter than the general caution bucket; the current project catalog marks them `dangerous`, which is conservative.

## 2. Keep Disabled

- Keep `EconomicGait` disabled until a Python wrapper method exists or a deliberate adapter implementation is added.
- Keep `TrajectoryFollow` disabled; it appears in a C++ example but not in the scanned Go2 SportClient header/Python wrapper.
- Keep `low_level_motor_control` out of scope.

## 3. Missing From Catalog

| API ID | Official | SDK Method | Recommendation |
| --- | --- | --- | --- |
| - | - | - | None by SDK API ID |

## 4. Missing From Go2Adapter

| Intent | Official | SDK Method | Recommendation |
| --- | --- | --- | --- |
| - | - | - | No safe real-robot catalog action is missing a Go2Adapter path |

## 5. Explicit Non-Changes

- Do not change any `dangerous` action to `safe`.
- Do not change `enable_real_robot`.
- Do not enable real robot execution for generated SDK actions.
- Do not remove SafetyController gates.
