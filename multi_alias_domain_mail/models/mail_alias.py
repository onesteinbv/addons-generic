import re
from collections import defaultdict

from odoo import api, exceptions, fields, models, _
from odoo.addons.mail.models.mail_alias import dot_atom_text
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import is_html_empty, remove_accents



class MailAlias(models.Model):
    _inherit = 'mail.alias'

    alias_domain_id = fields.Many2one(
            'mail.alias.domain', string='Alias Domain', ondelete='restrict',
            default=lambda self: self.env.company.alias_domain_id)
    alias_domain = fields.Char('Alias domain name', related='alias_domain_id.name')
    alias_full_name = fields.Char('Alias Email', compute='_compute_alias_full_name', store=True, index='btree_not_null')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')

    def init(self):
        """Make sure there aren't multiple records for the same name and alias
        domain. Not in _sql_constraint because COALESCE is not supported for
        PostgreSQL constraint. """
        self.env.cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS mail_alias_name_domain_unique
            ON mail_alias (alias_name, COALESCE(alias_domain_id, 0))
        """)

    @api.constrains('alias_domain_id', 'alias_force_thread_id', 'alias_parent_model_id',
                    'alias_parent_thread_id', 'alias_model_id')
    def _check_alias_domain_id_mc(self):
        """ Check for invalid alias domains based on company configuration.
        When having a parent record and/or updating an existing record alias
        domain should match the one used on the related record. """

        # in sudo, to be able to read alias_parent_model_id (ir.model)
        tocheck = self.sudo().filtered(lambda domain: domain.alias_domain_id.company_ids)
        if not tocheck:
            return

        # helpers to find owner / target models
        def _owner_model(alias):
            return alias.alias_parent_model_id.model

        def _owner_env(alias):
            return self.env[_owner_model(alias)]

        def _target_model(alias):
            return alias.alias_model_id.model

        def _target_env(alias):
            return self.env[_target_model(alias)]

        # fetch impacted records, classify by model
        recs_by_model = defaultdict(list)
        for alias in tocheck:
            # owner record (like 'project.project' for aliases creating new 'project.task')
            if alias.alias_parent_model_id and alias.alias_parent_thread_id:
                if _owner_env(alias)._mail_get_company_field():
                    recs_by_model[_owner_model(alias)].append(alias.alias_parent_thread_id)
            # target record (like 'mail.group' updating a given group)
            if alias.alias_model_id and alias.alias_force_thread_id:
                if _target_env(alias)._mail_get_company_field():
                    recs_by_model[_target_model(alias)].append(alias.alias_force_thread_id)

        # helpers to fetch owner / target with prefetching
        def _fetch_owner(alias):
            if alias.alias_parent_thread_id in recs_by_model[alias.alias_parent_model_id.model]:
                return _owner_env(alias).with_prefetch(
                    recs_by_model[_owner_model(alias)]
                ).browse(alias.alias_parent_thread_id)
            return None

        def _fetch_target(alias):
            if alias.alias_force_thread_id in recs_by_model[alias.alias_model_id.model]:
                return _target_env(alias).with_prefetch(
                    recs_by_model[_target_model(alias)]
                ).browse(alias.alias_force_thread_id)
            return None

        # check company domains are compatible
        for alias in tocheck:
            if owner := _fetch_owner(alias):
                company = owner[owner._mail_get_company_field()]
                if company and company.alias_domain_id != alias.alias_domain_id and alias.alias_domain_id.company_ids:
                    raise ValidationError(_(
                        "We could not create alias %(alias_name)s because domain "
                        "%(alias_domain_name)s belongs to company %(alias_company_names)s "
                        "while the owner document belongs to company %(company_name)s.",
                        alias_company_names=','.join(alias.alias_domain_id.company_ids.mapped('name')),
                        alias_domain_name=alias.alias_domain_id.name,
                        alias_name=alias.display_name,
                        company_name=company.name,
                    ))
            if target := _fetch_target(alias):
                company = target[target._mail_get_company_field()]
                if company and company.alias_domain_id != alias.alias_domain_id and alias.alias_domain_id.company_ids:
                    raise ValidationError(_(
                        "We could not create alias %(alias_name)s because domain "
                        "%(alias_domain_name)s belongs to company %(alias_company_names)s "
                        "while the target document belongs to company %(company_name)s.",
                        alias_company_names=','.join(alias.alias_domain_id.company_ids.mapped('name')),
                        alias_domain_name=alias.alias_domain_id.name,
                        alias_name=alias.display_name,
                        company_name=company.name,
                    ))

    @api.depends('alias_domain_id', 'alias_domain_id.name')
    def _compute_alias_domain(self):
        for rec in self:
            rec.alias_domain = rec.alias_domain_id.name

    @api.depends('alias_domain_id.name', 'alias_name')
    def _compute_alias_full_name(self):
        """ A bit like display_name, but without the 'inactive alias' UI display.
        Moreover it is stored, allowing to search on it. """
        for record in self:
            if record.alias_domain_id and record.alias_name:
                record.alias_full_name = f"{record.alias_name}@{record.alias_domain_id.name}"
            elif record.alias_name:
                record.alias_full_name = record.alias_name
            else:
                record.alias_full_name = False

    @api.depends('alias_domain', 'alias_name')
    def _compute_display_name(self):
        """ Return the mail alias display alias_name, including the catchall
        domain if found otherwise "Inactive Alias". e.g.`jobs@mail.odoo.com`
        or `jobs` or 'Inactive Alias' """
        for record in self:
            if record.alias_name and record.alias_domain:
                record.display_name = f"{record.alias_name}@{record.alias_domain}"
            elif record.alias_name:
                record.display_name = record.alias_name
            else:
                record.display_name = _("Inactive Alias")

    @api.model_create_multi
    def create(self, vals_list):
        """ Creates mail.alias records according to the values provided in
        ``vals`` but sanitize 'alias_name' by replacing certain unsafe
        characters; set default alias domain if not given.

        :raise UserError: if given (alias_name, alias_domain_id) already exists
          or if there are duplicates in given vals_list;
        """
        alias_names, alias_domains = [], []
        for vals in vals_list:
            vals['alias_name'] = self._sanitize_alias_name(vals.get('alias_name'))
            alias_names.append(vals['alias_name'])
            vals['alias_domain_id'] = vals.get('alias_domain_id', self.env.company.alias_domain_id.id)
            alias_domains.append(self.env['mail.alias.domain'].browse(vals['alias_domain_id']))

        self._check_unique(alias_names, alias_domains)
        return super().create(vals_list)

    def write(self, vals):
        """ Raise UserError with a meaningful message instead of letting the
        uniqueness constraint raise an SQL error. To check uniqueness we have
        to rebuild pairs of names / domains to validate, taking into account
        that a void alias_domain_id is acceptable (but also raises for
        uniqueness).
        """
        alias_names, alias_domains = [], []
        if 'alias_name' in vals:
            vals['alias_name'] = self._sanitize_alias_name(vals['alias_name'])
        if vals.get('alias_name') and self.ids:
            alias_names = [vals['alias_name']] * len(self)
        elif 'alias_name' not in vals and 'alias_domain_id' in vals:
            # avoid checking when writing the same value
            if [vals['alias_domain_id']] != self.alias_domain_id.ids:
                alias_names = self.filtered('alias_name').mapped('alias_name')

        if alias_names:
            tocheck_records = self if vals.get('alias_name') else self.filtered('alias_name')
            if 'alias_domain_id' in vals:
                alias_domains = [self.env['mail.alias.domain'].browse(vals['alias_domain_id'])] * len(tocheck_records)
            else:
                alias_domains = [record.alias_domain_id for record in tocheck_records]
            self._check_unique(alias_names, alias_domains)

        return super().write(vals)

    def _check_unique(self, alias_names, alias_domains):
        """ Check unicity constraint won't be raised, otherwise raise a UserError
        with a complete error message. Also check unicity against alias config
        parameters.

        :param list alias_names: a list of names (considered as sanitized
          and ready to be sent to DB);
        :param list alias_domains: list of alias_domain records under which
          the check is performed, as uniqueness is performed for given pair
          (name, alias_domain);
        """
        if len(alias_names) != len(alias_domains):
            msg = (f"Invalid call to '_check_unique': names and domains should make coherent lists, "
                   f"received {', '.join(alias_names)} and {', '.join(alias_domains.mapped('name'))}")
            raise ValueError(msg)

        # reorder per alias domain, keep only not void alias names (void domain also checks uniqueness)
        domain_to_names = defaultdict(list)
        for alias_name, alias_domain in zip(alias_names, alias_domains):
            if alias_name and alias_name in domain_to_names[alias_domain]:
                raise UserError(
                    _('Email aliases %(alias_name)s cannot be used on several records at the same time. Please update records one by one.',
                      alias_name=alias_name)
                )
            if alias_name:
                domain_to_names[alias_domain].append(alias_name)

        # matches existing alias
        domain = expression.OR([
            ['&', ('alias_name', 'in', alias_names), ('alias_domain_id', '=', alias_domain.id)]
            for alias_domain, alias_names in domain_to_names.items()
        ])
        if domain and self:
            domain = expression.AND([domain, [('id', 'not in', self.ids)]])
        existing = self.search(domain, limit=1) if domain else self.env['mail.alias']
        if not existing:
            return
        if existing.alias_parent_model_id and existing.alias_parent_thread_id:
            parent_name = self.env[existing.alias_parent_model_id.model].sudo().browse(
                existing.alias_parent_thread_id).display_name
            msg_begin = _(
                'Alias %(matching_name)s (%(current_id)s) is already linked with %(alias_model_name)s (%(matching_id)s) and used by the %(parent_name)s %(parent_model_name)s.',
                alias_model_name=existing.alias_model_id.name,
                current_id=self.ids if self else _('your alias'),
                matching_id=existing.id,
                matching_name=existing.display_name,
                parent_name=parent_name,
                parent_model_name=existing.alias_parent_model_id.name
            )
        else:
            msg_begin = _(
                'Alias %(matching_name)s (%(current_id)s) is already linked with %(alias_model_name)s (%(matching_id)s).',
                alias_model_name=existing.alias_model_id.name,
                current_id=self.ids if self else _('new'),
                matching_id=existing.id,
                matching_name=existing.display_name,
            )
        msg_end = _('Choose another value or change it on the other document.')
        raise UserError(f'{msg_begin} {msg_end}')

    @api.model
    def _sanitize_alias_name(self, name, is_email=False):
        """ Cleans and sanitizes the alias name. In some cases we want the alias
        to be a complete email instead of just a left-part (when sanitizing
        default.from for example). In that case we extract the right part and
        put it back after sanitizing the left part.

        :param str name: the alias name to sanitize;
        :param bool is_email: whether to keep a right part, otherwise only
          left part is kept;

        :return str: sanitized alias name
        """
        sanitized_name = name.strip() if name else ''
        if is_email:
            right_part = sanitized_name.lower().partition('@')[2]
        else:
            right_part = False
        if sanitized_name:
            sanitized_name = remove_accents(sanitized_name).lower().split('@')[0]
            # cannot start and end with dot
            sanitized_name = re.sub(r'^\.+|\.+$|\.+(?=\.)', '', sanitized_name)
            # subset of allowed characters
            sanitized_name = re.sub(r'[^\w!#$%&\'*+\-/=?^_`{|}~.]+', '-', sanitized_name)
            sanitized_name = sanitized_name.encode('ascii', errors='replace').decode()
        if not sanitized_name.strip():
            return False
        return f'{sanitized_name}@{right_part}' if is_email and right_part else sanitized_name
