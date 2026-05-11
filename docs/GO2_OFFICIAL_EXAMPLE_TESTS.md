# Go2 Official Example Tests

The files below were inspected only. No official example was run.

- Python example: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/third_party/unitree_sdk2_python/example/go2/high_level/go2_sport_client.py`
- C++ example: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/third_party/unitree_sdk2/example/go2/go2_sport_client.cpp`
- C++ trajectory example: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/third_party/unitree_sdk2/example/go2/go2_trajectory_follow.cpp`

| Language | File | Test | ID | SportClient calls | Motion/mode change | Risk | Allowed this round |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Python | go2_sport_client.py | damp | 0 | Damp() | yes | disabled | no |
| Python | go2_sport_client.py | stand_up | 1 | StandUp() | yes | safe | no |
| Python | go2_sport_client.py | stand_down | 2 | StandDown() | yes | safe | no |
| Python | go2_sport_client.py | move forward | 3 | Move(0.3,0,0) | yes | safe | no |
| Python | go2_sport_client.py | move lateral | 4 | Move(0,0.3,0) | yes | safe | no |
| Python | go2_sport_client.py | move rotate | 5 | Move(0,0,0.5) | yes | safe | no |
| Python | go2_sport_client.py | stop_move | 6 | StopMove() | no | safe | no |
| Python | go2_sport_client.py | hand stand | 7 | HandStand(True), HandStand(False) | yes | dangerous | no |
| Python | go2_sport_client.py | balanced stand | 9 | BalanceStand() | yes | safe | no |
| Python | go2_sport_client.py | recovery | 10 | RecoveryStand() | yes | safe | no |
| Python | go2_sport_client.py | left flip | 11 | LeftFlip() | yes | dangerous | no |
| Python | go2_sport_client.py | back flip | 12 | BackFlip() | yes | dangerous | no |
| Python | go2_sport_client.py | free walk | 13 | FreeWalk() | yes | caution | no |
| Python | go2_sport_client.py | free bound | 14 | FreeBound(True), FreeBound(False) | yes | dangerous | no |
| Python | go2_sport_client.py | free avoid | 15 | FreeAvoid(True), FreeAvoid(False) | yes | safe | no |
| Python | go2_sport_client.py | walk upright | 17 | WalkUpright(True), WalkUpright(False) | yes | caution | no |
| Python | go2_sport_client.py | cross step | 18 | CrossStep(True), CrossStep(False) | yes | caution | no |
| Python | go2_sport_client.py | free jump | 19 | FreeJump(True), FreeJump(False) | yes | dangerous | no |
| C++ | go2_sport_client.cpp | normal_stand | 0 | StandUp() | yes | safe | no |
| C++ | go2_sport_client.cpp | balance_stand | 1 | BalanceStand() | yes | safe | no |
| C++ | go2_sport_client.cpp | velocity_move | 2 | Move(0.3, 0, 0.3) | yes | safe | no |
| C++ | go2_sport_client.cpp | stand_down | 3 | StandDown() | yes | safe | no |
| C++ | go2_sport_client.cpp | stand_up | 4 | StandUp() | yes | safe | no |
| C++ | go2_sport_client.cpp | damp | 5 | Damp() | yes | disabled | no |
| C++ | go2_sport_client.cpp | recovery_stand | 6 | RecoveryStand() | yes | safe | no |
| C++ | go2_sport_client.cpp | sit | 7 | Sit() | yes | safe | no |
| C++ | go2_sport_client.cpp | rise_sit | 8 | RiseSit() | yes | safe | no |
| C++ | go2_sport_client.cpp | stop_move | 99 | StopMove() | no | safe | no |
| C++ | go2_trajectory_follow.cpp | trajectory_follow_example |  | TrajectoryFollow(path) | yes | disabled | no |

## Summary

- The Python Go2 example is an interactive motion test and includes posture, velocity, handstand, flip, gait, avoid, upright, cross-step, and jump branches.
- The C++ Go2 example runs a selected test mode in a loop and includes posture and velocity branches.
- `go2_trajectory_follow.cpp` calls `TrajectoryFollow(path)`, but that method is not present in the currently scanned Go2 SportClient header or Python wrapper, so the project keeps it disabled.
- These examples are useful source references only; they are not safe to run as part of this no-motion audit.
