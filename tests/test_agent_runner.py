from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pit_agents.product_intelligence import runner


def _block(type_, **kwargs):
    return SimpleNamespace(type=type_, **kwargs)


def _response(stop_reason, blocks):
    return SimpleNamespace(stop_reason=stop_reason, content=blocks)


class SingleTurnAgentTests(unittest.TestCase):
    def test_returns_text_from_a_single_call(self) -> None:
        fake_client = MagicMock()
        fake_client.messages.create.return_value = _response(
            "end_turn", [_block("text", text="Brief listo.")]
        )
        with patch.object(runner, "_client", return_value=fake_client):
            result = runner._run_single_turn_agent(instructions="SYSTEM", prompt="Haz un brief")

        self.assertEqual(result, "Brief listo.")
        fake_client.messages.create.assert_called_once()
        call_kwargs = fake_client.messages.create.call_args.kwargs
        self.assertEqual(call_kwargs["system"], "SYSTEM")
        self.assertEqual(call_kwargs["messages"], [{"role": "user", "content": "Haz un brief"}])
        self.assertNotIn("tools", call_kwargs)


class ContextAgentTests(unittest.TestCase):
    def test_calls_tool_and_returns_final_text(self) -> None:
        fake_client = MagicMock()
        fake_client.messages.create.side_effect = [
            _response(
                "tool_use",
                [_block("tool_use", id="tu_1", name="load_scientific_context", input={})],
            ),
            _response("end_turn", [_block("text", text="Hallazgos científicos.")]),
        ]
        with patch.object(runner, "_client", return_value=fake_client):
            result = runner._run_context_agent(
                instructions="SCI_SYSTEM",
                prompt="Evalúa la evidencia",
                tool_name="load_scientific_context",
                domain="scientific",
            )

        self.assertEqual(result, "Hallazgos científicos.")
        self.assertEqual(fake_client.messages.create.call_count, 2)

        second_call_messages = fake_client.messages.create.call_args_list[1].kwargs["messages"]
        # [user prompt, assistant tool_use, user tool_result]
        self.assertEqual(len(second_call_messages), 3)
        tool_result_message = second_call_messages[2]
        self.assertEqual(tool_result_message["role"], "user")
        self.assertEqual(len(tool_result_message["content"]), 1)
        tool_result = tool_result_message["content"][0]
        self.assertEqual(tool_result["type"], "tool_result")
        self.assertEqual(tool_result["tool_use_id"], "tu_1")
        payload = json.loads(tool_result["content"])
        self.assertEqual(payload["status"], "not_configured")

    def test_raises_if_max_turns_exceeded_without_finishing(self) -> None:
        fake_client = MagicMock()
        never_ending_tool_use = _response(
            "tool_use",
            [_block("tool_use", id="tu_x", name="load_scientific_context", input={})],
        )
        fake_client.messages.create.return_value = never_ending_tool_use
        with patch.object(runner, "_client", return_value=fake_client), patch.object(
            runner, "MAX_TURNS", 2
        ):
            with self.assertRaises(RuntimeError):
                runner._run_context_agent(
                    instructions="SCI_SYSTEM",
                    prompt="Evalúa la evidencia",
                    tool_name="load_scientific_context",
                    domain="scientific",
                )


class OrchestratorTests(unittest.TestCase):
    def test_delegates_to_sub_agents_and_returns_both_tool_results_in_one_message(self) -> None:
        fake_client = MagicMock()
        fake_client.messages.create.side_effect = [
            _response(
                "tool_use",
                [
                    _block(
                        "tool_use",
                        id="tu_sci",
                        name="scientific_evidence",
                        input={"task": "evalua ciencia"},
                    ),
                    _block(
                        "tool_use",
                        id="tu_mkt",
                        name="market_intelligence",
                        input={"task": "evalua mercado"},
                    ),
                ],
            ),
            _response("end_turn", [_block("text", text="# Ficha de Oportunidad\n...")]),
        ]

        mock_sci = MagicMock(return_value="ciencia ok")
        mock_mkt = MagicMock(return_value="mercado ok")
        with patch.object(runner, "_client", return_value=fake_client), patch.dict(
            runner._DELEGATE_HANDLERS,
            {"scientific_evidence": mock_sci, "market_intelligence": mock_mkt},
        ):
            result = runner._run_orchestrator("Analiza esta iniciativa")

        self.assertEqual(result, "# Ficha de Oportunidad\n...")
        mock_sci.assert_called_once_with("evalua ciencia")
        mock_mkt.assert_called_once_with("evalua mercado")

        second_call_messages = fake_client.messages.create.call_args_list[1].kwargs["messages"]
        tool_result_message = second_call_messages[-1]
        self.assertEqual(tool_result_message["role"], "user")
        self.assertEqual(len(tool_result_message["content"]), 2)
        contents_by_id = {c["tool_use_id"]: c["content"] for c in tool_result_message["content"]}
        self.assertEqual(contents_by_id["tu_sci"], "ciencia ok")
        self.assertEqual(contents_by_id["tu_mkt"], "mercado ok")

    def test_raises_if_max_turns_exceeded(self) -> None:
        fake_client = MagicMock()
        fake_client.messages.create.return_value = _response(
            "tool_use",
            [_block("tool_use", id="tu_x", name="build_product_brief", input={"task": "x"})],
        )
        with patch.object(runner, "_client", return_value=fake_client), patch.dict(
            runner._DELEGATE_HANDLERS, {"build_product_brief": MagicMock(return_value="brief")}
        ), patch.object(runner, "MAX_TURNS", 2):
            with self.assertRaises(RuntimeError):
                runner._run_orchestrator("Analiza esta iniciativa")


if __name__ == "__main__":
    unittest.main()
