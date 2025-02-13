# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Helpdesk Mail",
    "summary": "Adds the option to send out helpdesk ticket updates to contacts by email.",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "category": "After-Sales",
    "author": "Onestein BV",
    "website": "https://www.onestein.eu",
    "depends": ["helpdesk_mgmt", "base_automation", "mail_layout_force"],
    "data": [
        "data/mail_template.xml",
        "data/automated_action.xml",
        "views/helpdesk_ticket_team_view.xml",
        "views/helpdesk_ticket_view.xml",
    ],
    "installable": True,
}
