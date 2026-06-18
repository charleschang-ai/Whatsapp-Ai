from odoo import models, fields


class WhatsAppAccount(models.Model):
    _inherit = 'whatsapp.account'

    enable_ai = fields.Boolean(
        string='Enable AI customer service',
        default=False,
        help='Once enabled, WhatsApp text messages to this account will be automatically replied to by the selected AI Agent by default.',
    )
    ai_agent_id = fields.Many2one(
        comodel_name='ai.agent',
        string='AI Agent',
        help='Choose an AI Agent responsible for automatic responses.',
    )
