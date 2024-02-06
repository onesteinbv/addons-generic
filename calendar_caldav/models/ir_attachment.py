from urllib.parse import urlparse

from icalendar.prop import vUri

from odoo import api, fields, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    caldav_params = fields.Serialized()

    @api.model
    @api.returns("ir.attachment")
    def import_caldav_attachments(self, attachments, event):
        if type(attachments) is not list:
            attachments = [attachments]
        res = self.env["ir.attachment"]
        for attachment in attachments:
            if type(attachment) is not vUri:
                continue
            res += self._import_caldav_attachment(attachment, event)
        return res

    @api.model
    def _import_caldav_attachment(self, attachment, event):
        if type(attachment) is not vUri:
            raise NotImplementedError()

        values = self.caldav_vuri_to_odoo(attachment, event)
        existing_attachments = self.search(
            [
                ("type", "=", "url"),
                ("url", "=", values["url"]),
                ("res_model", "=", "calendar.event"),
                ("res_id", "=", event.id),
            ]
        )
        if not existing_attachments:
            existing_attachments = self.create(values)
        return existing_attachments

    @api.model
    def caldav_vuri_to_odoo(self, attachment, event):
        attachment_parsed = urlparse(attachment)
        url = attachment  # is instance of str
        if not attachment_parsed.scheme:
            calendar_url_parsed = urlparse(event.caldav_calendar_id.url)
            url = "%s://%s%s" % (
                calendar_url_parsed.scheme,
                calendar_url_parsed.netloc,
                attachment,
            )

        name = attachment.params.get("FILENAME", attachment).split("/")[-1]
        return {
            "name": name,
            "type": "url",
            "url": url,
            "res_model": "calendar.event",
            "res_id": event.id,
            "caldav_params": attachment.params,
        }

    def to_caldav(self):
        res = []
        for attachment in self.filtered(lambda a: a.type == "url"):
            vuri = vUri(attachment.url)
            vuri.params.update(attachment.caldav_params)
            res.append(vuri)
        return res
