from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ContractContract(models.Model):
    _inherit = "contract.contract"

    contract_payment_subscription_id = fields.Many2one(
        "contract.payment.subscription",
        readonly=True,
    )
    is_provider_subscription_terminated = fields.Boolean()

    @api.model
    def cron_update_contract_payment_subscriptions(self):
        date_ref = fields.Date.context_today(self)
        contracts = self.search(
            [
                ("generation_type", "=", "invoice"),
                ("contract_payment_subscription_id", "!=", False),
                "|",
                ("recurring_next_date", "<=", date_ref),
                ("contract_line_ids.last_date_invoiced", "=", date_ref),
            ]
        )
        companies = set(contracts.mapped("company_id"))
        for company in companies:
            contracts_to_update = contracts.filtered(
                lambda c: c.company_id == company
                and (not c.date_end or c.recurring_next_date <= c.date_end)
            ).with_company(company)
            for contract in contracts_to_update:
                contract.update_contract_payments_and_subscription_status(date_ref)
        return True

    def update_contract_payments_and_subscription_status(self, date_ref):
        # This method needs to be extended in each provider module.
        # This method updates the payments, their status and subscription status for contracts
        return True

    @api.model
    def cron_terminate_provider_subscriptions(self):
        date_ref = fields.Date.context_today(self)
        contracts = self.search(
            [
                ("contract_payment_subscription_id", "!=", False),
                ("is_provider_subscription_terminated", "=", False),
                ("terminate_date", "<=", date_ref),
            ]
        )
        for contract in contracts:
            contract.terminate_provider_subscription()
        return True

    def _terminate_contract(
        self, terminate_reason_id, terminate_comment, terminate_date
    ):
        res = super()._terminate_contract(
            terminate_reason_id, terminate_comment, terminate_date
        )
        if self.contract_payment_subscription_id:
            if self.terminate_date <= fields.Date.context_today(self):
                self.terminate_provider_subscription()
        return res

    @api.model
    def terminate_provider_subscription(self):
        # This method needs to be extended in each provider module.
        # This method cancels/terminates the contract/subscription on the provider end
        return True

    def action_cancel_contract_termination(self):
        if (
            self.contract_payment_subscription_id
            and self.is_provider_subscription_terminated
        ):
            raise UserError(
                _(
                    "Terminated contracts with provider subscription also terminated cannot be "
                    "renewed.Please generate a new contract"
                )
            )
        return super().action_cancel_contract_termination()
