from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    type_mapping = {
        "follower": ["member_type_follower"],
        "applicant": ["member_type_applicant"],
        "collaborator": ["member_type_collaborator"],
        "committee": ["member_type_committee"],
        "applicant_follower": ["member_type_applicant", "member_type_follower"],
        "collaborator_follower": ["member_type_collaborator", "member_type_follower"],
    }
    resolved_ids = {}
    for xml_ids in type_mapping.values():
        for xml_id in xml_ids:
            if xml_id not in resolved_ids:
                record = env.ref(f"membership_group.{xml_id}", raise_if_not_found=False)
                if record:
                    resolved_ids[xml_id] = record.id
    cr.execute("SELECT id, type FROM membership_group_member WHERE type IS NOT NULL")
    for row in cr.dictfetchall():
        old_type = row["type"]
        if old_type in type_mapping:
            new_type_ids = [
                resolved_ids[xml_id]
                for xml_id in type_mapping[old_type]
                if xml_id in resolved_ids
            ]
            if new_type_ids:
                env["membership.group.member"].browse(row["id"]).write(
                    {"type_ids": [(6, 0, new_type_ids)]}
                )
