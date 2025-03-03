import ast
import base64
import re

from odoo import _, api, fields, models, tools, Command
from odoo.exceptions import ValidationError
from odoo.osv import expression

def parse_res_ids(res_ids):
    """ Returns the already valid list/tuple of int or returns the literal eval
    of the string as a list/tuple of int. Void strings / missing values are
    evaluated as an empty list.

    :param str|tuple|list res_ids: a list of ids, tuple or list;

    :raise: ValidationError if the provided res_ids is an incorrect type or
      invalid format;

    :return list: list of ids
    """
    if tools.is_list_of(res_ids, int) or not res_ids:
        return res_ids
    error_msg = _("Invalid res_ids %(res_ids_str)s (type %(res_ids_type)s)",
                  res_ids_str=res_ids,
                  res_ids_type=type(res_ids))
    try:
        res_ids = ast.literal_eval(res_ids)
    except Exception as e:
        raise ValidationError(error_msg) from e

    if not tools.is_list_of(res_ids, int):
        raise ValidationError(error_msg)

    return res_ids

class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    composition_batch = fields.Boolean(
        'Batch composition', compute='_compute_composition_batch')  # more than 1 record (raw source)
    res_ids = fields.Text('Related Document IDs', compute='_compute_res_ids', readonly=False, store=True)
    record_alias_domain_id = fields.Many2one(
        'mail.alias.domain', 'Alias Domain',
        compute='_compute_record_environment', readonly=False, store=True)  # useful only in monorecord comment mode

    @api.constrains('res_ids')
    def _check_res_ids(self):
        """ Check res_ids is a valid list of integers (or Falsy). """
        for composer in self:
            composer._evaluate_res_ids()

    @api.depends('res_ids')
    def _compute_composition_batch(self):
        """ Determine if batch mode is activated:

          * using res_domain: always batch (even if result is singleton at a
            given time, it is user and time dependent, hence batch);
          * res_ids: if more than one item in the list (void and singleton are
            not batch);
        """
        for composer in self:
            res_ids = composer._evaluate_res_ids()
            composer.composition_batch = len(res_ids) > 1 if res_ids else False

    @api.depends('composition_mode', 'parent_id')
    def _compute_res_ids(self):
        """ Computation may come from parent in comment mode, if set. It takes
        the parent message's res_id. Otherwise the composer uses the 'active_ids'
        context key, unless it is too big to be stored in database. Indeed
        when invoked for big mailings, 'active_ids' may be a very big list.
        Support of 'active_ids' when sending is granted in order to not always
        rely on 'res_ids' field. When 'active_ids' is not present, fallback
        on 'active_id'. """
        for composer in self.filtered(lambda composer: not composer.res_ids):
            if composer.parent_id and composer.composition_mode == 'comment':
                composer.res_ids = f"{[composer.parent_id.res_id]}"
            else:
                active_res_ids = parse_res_ids(self.env.context.get('active_ids'))
                # beware, field is limited in storage, usage of active_ids in context still required
                if active_res_ids and len(active_res_ids) <= self._batch_size:
                    composer.res_ids = f"{self.env.context['active_ids']}"
                elif not active_res_ids and self.env.context.get('active_id'):
                    composer.res_ids = f"{[self.env.context['active_id']]}"

    @api.depends('composition_mode', 'model',  'res_ids')
    def _compute_record_environment(self):
        """ In monorecord mode, fetch record company and the linked alias domain,
        easing future processing notably at post and notification sending time.

        In batch mode it makes no sense to compute a single company, it will be
        dynamically generated. """
        toreset = self.filtered(
            lambda comp: comp.record_alias_domain_id and comp.composition_batch
        )
        if toreset:
            toreset.record_alias_domain_id = False

        toupdate = self.filtered(
            lambda comp: not comp.composition_batch
        )
        for composer in toupdate:
            res_ids = composer._evaluate_res_ids()
            if composer.model in self.env and len(res_ids) == 1:
                record = self.env[composer.model].browse(res_ids)
                composer.record_alias_domain_id = record._mail_get_alias_domains(
                    default_company=self.env.company
                )[record.id]

    def get_mail_values(self, res_ids):
        mail_values = super().get_mail_values(res_ids=res_ids)
        mass_mail_mode = self.composition_mode == 'mass_mail'
        for res_id in res_ids:
            if mass_mail_mode:
                mail_values[res_id].update(record_alias_domain_id=self.record_alias_domain_id.id)
        return mail_values

    def _evaluate_res_ids(self):
        """ Parse composer res_ids, which can be: an already valid list or
        tuple (generally in code), a list or tuple as a string (coming from
        actions). Void strings / missing values are evaluated as an empty list.

        Note that 'active_ids' context key is supported at this point as mailing
        on big ID list would create issues if stored in database.

        Another context key 'composer_force_res_ids' is temporarily supported
        to ease support of accounting wizard, while waiting to implement a
        proper solution to language management.

        :return: a list of IDs (empty list in case of falsy strings)"""
        self.ensure_one()
        return parse_res_ids(
            self.env.context.get('composer_force_res_ids') or
            self.res_ids or
            self.env.context.get('active_ids')
        ) or []