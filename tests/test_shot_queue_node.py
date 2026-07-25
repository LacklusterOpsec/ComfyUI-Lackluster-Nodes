import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("lackluster_shot_queue_v2", ROOT / "lackluster_shot_queue_v2.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_queue_adds_and_limits_items():
    node = module.LacklusterShotQueueNodeV2()

    result = node.execute(
        camera_preset="front_close_up",
        add_to_queue=True,
        run_queue=False,
        clear_queue=False,
        custom_prefix="<sks>",
        sequence_json="[]",
        unique_id="test",
    )

    assert result["result"][3] == 1
    assert result["ui"]["queue_count"] == 1

    queue_json = result["ui"]["sequence_json"]
    for preset_name in ["front_medium", "front_wide", "low_angle_hero", "low_angle_close_up", "high_angle_shot", "over_shoulder", "right_profile", "back_view", "left_profile", "three_quarter_front"]:
        queue_result = node.execute(
            camera_preset=preset_name,
            add_to_queue=True,
            run_queue=False,
            clear_queue=False,
            custom_prefix="<sks>",
            sequence_json=queue_json,
            unique_id="test",
        )
        queue_json = queue_result["ui"]["sequence_json"]

    final_result = node.execute(
        camera_preset="front_close_up",
        add_to_queue=True,
        run_queue=False,
        clear_queue=False,
        custom_prefix="<sks>",
        sequence_json=queue_json,
        unique_id="test",
    )

    queued_items = final_result["ui"]["queue_items"]
    assert len(queued_items) == 10
    assert queued_items[0]["preset"] == "front_close_up"
    assert queued_items[-1]["preset"] == "left_profile"
