from odoo import fields, models


class WebsiteSnippetFilter(models.Model):
    _inherit = "website.snippet.filter"

    def _filter_records_to_values(self, records, is_sample=False):
        meta_data = self._get_filter_meta_data()
        values = []
        model = self.env[self.model_name]
        Website = self.env["website"]
        for record in records:
            data = {}
            for field_name, field_widget in meta_data.items():
                field = model._fields.get(field_name)
                if field and field.type in ("binary", "image"):
                    if is_sample:
                        raw = record[field_name]
                        if field_name in record and raw and raw is not True and raw is not False:
                            data[field_name] = raw.decode("utf8")
                        else:
                            data[field_name] = "/web/image"
                    else:
                        data[field_name] = Website.image_url(record, field_name)
                elif field_widget == "monetary":
                    model_currency = None
                    if field and field.type == "monetary":
                        model_currency = record[field.get_currency_field(record)]
                    elif "currency_id" in model._fields:
                        model_currency = record["currency_id"]
                    if model_currency:
                        website_currency = self._get_website_currency()
                        data[field_name] = model_currency._convert(
                            record[field_name],
                            website_currency,
                            Website.get_current_website().company_id,
                            fields.Date.today(),
                        )
                    else:
                        data[field_name] = record[field_name]
                else:
                    data[field_name] = record[field_name]
            data["call_to_action_url"] = False
            if not is_sample:
                data["call_to_action_url"] = (
                    "website_url" in record and record["website_url"]
                )
            data["_record"] = record
            values.append(data)
        return values

    def _render(self, template_key, limit, search_domain=None, with_sample=False, **custom_template_data):
        if with_sample and search_domain:
            records = self._prepare_values(limit=1, search_domain=search_domain)
            if not records:
                with_sample = False

        fragments = super()._render(
            template_key, limit,
            search_domain=search_domain,
            with_sample=with_sample,
            **custom_template_data,
        )
        if not fragments:
            return [
                '<div class="text-center text-muted py-4 w-100">'
                '<p class="mb-0">No members found.</p>'
                '<small>Make sure members are published and have an active membership in the selected group.</small>'
                '</div>'
            ]
        return fragments
