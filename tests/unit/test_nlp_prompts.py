from combatrl.nlp.prompts import build_profile_parser_prompt


def test_prompt_mentions_allowed_axes() -> None:
    prompt = build_profile_parser_prompt("play aggressively")

    for axis in ("aggression", "caution", "cohesion", "protectiveness", "focus_fire", "greed"):
        assert axis in prompt


def test_prompt_says_json_only() -> None:
    assert "Output JSON only" in build_profile_parser_prompt("protect ally")


def test_prompt_forbids_raw_actions() -> None:
    prompt = build_profile_parser_prompt("attack now")

    assert "Do not output raw actions" in prompt
    assert "action IDs" in prompt


def test_prompt_forbids_invented_abilities() -> None:
    assert "Do not invent new abilities" in build_profile_parser_prompt("cast fireball")


def test_prompt_says_tactical_execution_happens_elsewhere() -> None:
    assert "Tactical execution is handled elsewhere" in build_profile_parser_prompt("kite")
