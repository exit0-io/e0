def test_ok_envelope_shape(e0mod):
    result = e0mod.ok("status", {"a": 1}, "all good")
    assert result == {
        "ok": True,
        "command": "status",
        "data": {"a": 1},
        "message": "all good",
    }


def test_problem_envelope_shape(e0mod):
    result = e0mod.problem("start", "Task not found.", "Run 'e0 catalog'.")
    assert result["ok"] is False
    assert result["command"] == "start"
    assert result["problem"] == "Task not found."
    assert result["guidance"] == "Run 'e0 catalog'."
    assert "Task not found." in result["message"]
    assert "Run 'e0 catalog'." in result["message"]


def test_unknown_command_is_a_problem_not_a_crash(run_e0, tmp_path):
    payload, code = run_e0(["definitely-not-a-command"], tmp_path)
    assert code == 0
    assert payload["ok"] is False
    assert "definitely-not-a-command" in payload["problem"]


def test_no_arguments_is_not_a_crash(run_e0, tmp_path):
    payload, code = run_e0([], tmp_path)
    assert code == 0
    assert isinstance(payload["ok"], bool)


def test_handler_exception_is_caught_and_reported(e0mod, capsys):
    def exploding_handler(args):
        raise RuntimeError("boom")

    e0mod.COMMANDS["explode"] = exploding_handler
    code = e0mod.main(["explode"])
    captured = capsys.readouterr()
    payload = __import__("json").loads(captured.out)

    assert code == 0
    assert payload["ok"] is False
    assert "RuntimeError" in payload["problem"]
    assert "boom" in payload["problem"]


def test_help_lists_every_registered_command(run_e0, tmp_path, e0mod):
    payload, code = run_e0(["help"], tmp_path)
    assert code == 0
    assert payload["ok"] is True
    for name in e0mod.COMMANDS:
        assert name in payload["data"]["commands"]
