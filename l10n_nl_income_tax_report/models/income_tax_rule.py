from ast import literal_eval

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval, test_python_expr


class IncomeTaxRule(models.Model):
    _name = "l10n.nl.income.tax.rule"
    _description = "Income Tax Rule"
    _order = "sequence, id"

    year_id = fields.Many2one(comodel_name="l10n.nl.income.tax.year", required=True)
    currency_id = fields.Many2one(related="year_id.currency_id")
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    description = fields.Html()
    type = fields.Selection(
        selection=[
            ("fixed", "Fixed"),
            ("percentual", "Percentual"),
            ("python", "Python"),
        ],
        required=True,
    )
    is_tax = fields.Boolean()
    is_deduction = fields.Boolean()
    amount = fields.Float(string="Percentage")
    amount_monetary = fields.Monetary(currency_field="currency_id", string="Constant")
    apply_from = fields.Monetary(currency_field="currency_id", string="From")
    apply_to = fields.Monetary(currency_field="currency_id", string="To")

    apply_min = fields.Monetary(currency_field="currency_id", string="Min.")
    apply_max = fields.Monetary(currency_field="currency_id", string="Max.")
    apply_domain = fields.Text(string="Domain")

    code = fields.Text()

    @api.constrains("code")
    def _constrain_code(self):
        for rule in self.filtered(lambda r: r.type == "python"):
            err = test_python_expr(expr=rule.code.strip(), mode="exec")
            if err:
                raise ValidationError(err)

    @api.constrains("apply_from", "apply_to")
    def _constrain_from_to(self):
        for rule in self:
            if rule.apply_from < 0:
                raise ValidationError(_("'From' must be greater than 0"))
            if rule.apply_to < 0:
                raise ValidationError(_("'To' must be greater than 0"))
            if (rule.apply_from and rule.apply_to) and rule.apply_to < rule.apply_from:
                raise ValidationError(_("'To' must be greater than 'From'"))

    @api.constrains("apply_min", "apply_max")
    def _constrain_min_max(self):
        for rule in self:
            if rule.apply_min < 0:
                raise ValidationError(_("'Min.' must be greater than 0"))
            if rule.apply_max < 0:
                raise ValidationError(_("'Max.' must be greater than 0"))
            if (rule.apply_min and rule.apply_max) and rule.apply_max < rule.apply_min:
                raise ValidationError(_("'To' must be greater than 'From'"))

    def _check_is_applicable(self, taxable_income, report):
        self.ensure_one()

        # Check min. max.
        if self.apply_min or self.apply_max:
            if self.apply_min and not self.apply_max:
                if taxable_income < self.apply_min:
                    return False
            elif self.apply_min > taxable_income or taxable_income > self.apply_max:
                return False

        # Check domain
        if self.apply_domain and not bool(
            report.filtered_domain(literal_eval(self.apply_domain))
        ):
            return False
        return True

    def apply(self, taxable_income, report):
        logs = []
        total_tax = 0
        for rule in self:
            if not rule._check_is_applicable(taxable_income, report):
                continue
            method_name = "_apply_%s" % rule.type
            if not hasattr(rule, method_name):
                raise Exception(_("Method %s does not exists.") % method_name)
            method = getattr(rule, method_name)
            deduction, tax = method(taxable_income)
            taxable_income -= deduction
            logs.append(
                {
                    "rule_id": rule.id,
                    "taxable_income": taxable_income,
                    "tax": tax,
                    "deduction": deduction,
                }
            )
            total_tax += tax
        return taxable_income, total_tax, logs

    def _apply_fixed(self, taxable_income):
        self.ensure_one()
        tax = 0
        deduction = 0

        if self.is_deduction:
            deduction = self.amount_monetary
        if self.is_tax:
            tax = self.amount_monetary
        return deduction, tax

    def _apply_percentual(self, taxable_income):
        self.ensure_one()

        applicable_income = taxable_income
        if self.apply_from or self.apply_to:
            if self.apply_from and not self.apply_to:
                applicable_income -= self.apply_from
            else:
                max_applicable = self.apply_to - self.apply_from
                income_range = applicable_income - self.apply_from
                applicable_income = min(max_applicable, income_range)
            if applicable_income < 0:
                applicable_income = 0
        amount = (self.amount / 100) * applicable_income + self.amount_monetary
        tax = 0
        deduction = 0
        if self.is_deduction:
            deduction = amount
        if self.is_tax:
            tax = amount
        return deduction, tax

    def _get_eval_context(self, **kwargs):
        return {"self": self, **kwargs}

    def _apply_python(self, taxable_income):
        self.ensure_one()
        context = self._get_eval_context(taxable_income=taxable_income)
        safe_eval(self.code.strip(), context, mode="exec", nocopy=True)
        return context.get("deduction", 0), context.get("tax", 0)
