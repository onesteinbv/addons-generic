# Copyright (C) 2016 Onestein (<http://www.onestein.eu>).
from collections import defaultdict

from odoo import api, fields, models
from odoo.tools import SQL


class AccountAccount(models.Model):
    _inherit = "account.account"
    _order = "sort_code, code, placeholder_code"

    group_id = fields.Many2one(
        "account.group",
        search="_search_group_id",
    )
    referentiecode = fields.Char()
    sort_code = fields.Char(string="Sorting code")

    def _search_group_id(self, operator, value):
        if operator == "=" and not value:
            return [("id", "=", False)]
        if operator in ("=", "in"):
            group_ids = [value] if operator == "=" else (value or [])
            if not group_ids:
                return [("id", "=", False)]
            mapping = self._get_group_to_accounts_mapping()
            account_ids = []
            for gid in group_ids:
                account_ids.extend(mapping.get(gid, []))
            return [("id", "in", account_ids)]
        if operator in ("!=", "not in"):
            group_ids = [value] if operator == "!=" else (value or [])
            if not group_ids:
                return [(1, "=", 1)]
            mapping = self._get_group_to_accounts_mapping()
            account_ids = []
            for gid in group_ids:
                account_ids.extend(mapping.get(gid, []))
            return [("id", "not in", account_ids)]
        raise NotImplementedError(
            f"Search on group_id with operator '{operator}' is not supported."
        )

    def _get_group_to_accounts_mapping(self):
        cache_attr = "_group_to_accounts_cache"
        root_company_id = self.env.company.root_id.id
        cached = getattr(self.env, cache_attr, None)
        if cached and cached.get("company_id") == root_company_id:
            return cached["mapping"]
        company_key = str(root_company_id)
        results = self.env.execute_query(
            SQL(
                """
                SELECT DISTINCT ON (aa.id)
                       aa.id AS account_id,
                       agroup.id AS group_id
                FROM account_account aa
                LEFT JOIN account_group agroup
                    ON agroup.code_prefix_start <= LEFT(
                        aa.code_store->>%(company_key)s,
                        char_length(agroup.code_prefix_start)
                    )
                    AND agroup.code_prefix_end >= LEFT(
                        aa.code_store->>%(company_key)s,
                        char_length(agroup.code_prefix_end)
                    )
                    AND agroup.company_id = %(root_company_id)s
                WHERE aa.code_store->>%(company_key)s IS NOT NULL
                ORDER BY aa.id,
                         char_length(agroup.code_prefix_start) DESC,
                         agroup.id
                """,
                company_key=company_key,
                root_company_id=root_company_id,
            )
        )
        mapping = defaultdict(list)
        for account_id, group_id in results:
            if group_id:
                mapping[group_id].append(account_id)
        setattr(
            self.env,
            cache_attr,
            {
                "company_id": root_company_id,
                "mapping": mapping,
            },
        )
        return mapping

    def write(self, vals):
        resp = super().write(vals)

        for rec in self.filtered(
            lambda acc: not acc.referentiecode
            and acc.group_id
            and acc.group_id.referentiecode
        ):
            rec.referentiecode = rec.group_id.referentiecode
        if not self._context.get("group_allowed_journal_change"):
            self.group_set_allowed_journals()
        return resp

    def group_set_allowed_journals(self):
        for rec in self.filtered(
            lambda a: a.group_id and a.group_id.auto_allowed_journals
        ):
            rec.with_context(
                group_allowed_journal_change=True
            ).allowed_journal_ids = rec.group_id.active_allowed_journal_ids

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self._context.get("group_allowed_journal_change"):
            records.group_set_allowed_journals()
        return records
