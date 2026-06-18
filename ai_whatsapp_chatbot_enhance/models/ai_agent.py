from odoo import models
from types import SimpleNamespace
import re
import logging
from odoo.addons.ai.utils.llm_api_service import LLMApiService

_logger = logging.getLogger(__name__)
TEMPERATURE_MAP = {
    'analytical': 0.2,
    'balanced': 0.5,
    'creative': 0.8,
}


class AIAgentAdvanced(models.Model):
    _inherit = 'ai.agent'

    def _generate_response_for_whatsapp(self, mail_message, channel):
        self.ensure_one()
        mail_message = SimpleNamespace(body=mail_message)
        prompt, session_info_context = self._parse_user_message(mail_message)
        try:
            response = self.with_context(discuss_channel=channel)._generate_whatsapp_response(
                prompt=prompt,
                chat_history=[{'content': session_info_context, 'role': 'user'}] + self._retrieve_chat_history(channel),
                extra_system_context=self._build_extra_system_context(channel),
                is_whatsapp=True
            )
        except Exception:
            if self.env.user._is_internal():
                raise
            return self.env._("Oops, it looks like our AI is unreachable")

        if not response:
            return ""

        combined = "\n\n".join(msg for msg in response if msg)

        return combined

    def _generate_whatsapp_response(self, prompt, chat_history=None, extra_system_context="", is_whatsapp=True):
        """Generate an AI response for the given user prompt.

        This method orchestrates the complete response generation flow:
        1. Constructs system context from agent settings and additional context
        2. Retrieves relevant RAG context from sources (if any)
        3. Sends the complete conversation to the LLM API
        4. Processes any tool calls in the response, executing them and continuing the conversation
        5. Stops when the LLM provides a final response or all tools request termination

        :param prompt: The user's input prompt
        :param chat_history: Previous conversation messages to include as context
        :param extra_system_context: Additional system instructions to include
        :return: List of response messages from the LLM and/or tool termination messages
        :raises UserError: If no LLM provider is found for the selected model
        """
        self.ensure_one()
        _logger.debug("[AI Prompt] %s", prompt)
        system_messages = self._build_system_context(extra_system_context=extra_system_context)
        if rag_context := self._build_rag_context(prompt):
            system_messages.extend(rag_context)
        llm_response = LLMApiService(env=self.env, provider=self._get_provider()).request_llm(
            self.llm_model,
            system_messages,
            [],
            inputs=(chat_history or []) + [{'role': 'user', 'content': prompt}],
            tools=self.sudo().topic_ids.tool_ids._get_ai_tools(),
            temperature=TEMPERATURE_MAP[self.response_style],
        )
        if rag_context:
            llm_response = self._get_llm_response_with_sources(llm_response)

        return llm_response


