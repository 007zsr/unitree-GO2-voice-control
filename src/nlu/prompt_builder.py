from __future__ import annotations


class PromptBuilder:
    def build(self, text: str) -> list[dict[str, str]]:
        system = (
            "You are the semantic parser for a Unitree Go2 voice-control system. "
            "The input may be Chinese, English, or mixed Chinese/English. "
            "Return exactly one JSON object and nothing else. "
            "Do not output Python code, SDK names, Unitree API calls, or explanations outside JSON. "
            "Allowed intents are stop, stand_up, sit_down, move_forward, move_backward, "
            "turn_left, turn_right, status_report, none, unknown, and unknown_relative_move. "
            "If the user gives multiple sequential commands, return at most three commands. "
            "If the user says 'come here' without reliable direction, set needs_confirmation=true "
            "and do not infer move_forward. If the user says they are on the robot's left or right, "
            "you may infer only turn_left or turn_right, not forward movement. "
            "If the text is not a robot-control command, set is_command=false and intent=none. "
            "If the request is dangerous, attacking, crashing, jumping, flipping, or high speed, "
            "set dangerous=true."
        )
        user = (
            "Parse this user text into this exact JSON schema:\n"
            '{"is_command":true,"plan_type":"sequence","commands":['
            '{"intent":"turn_right","duration_sec":0.7,"speed_level":"slow",'
            '"source_span":"turn right","confidence":0.91,"inferred":false},'
            '{"intent":"turn_left","duration_sec":0.7,"speed_level":"slow",'
            '"source_span":"turn left","confidence":0.89,"inferred":false}],'
            '"intent":"turn_right","duration_sec":0.7,"speed_level":"slow",'
            '"source_language":"en","confidence":0.89,"need_clarification":false,'
            '"dangerous":false,"needs_confirmation":false,'
            '"reason":"Two explicit sequential commands were found."}\n'
            f"User text: {text}"
        )
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]
