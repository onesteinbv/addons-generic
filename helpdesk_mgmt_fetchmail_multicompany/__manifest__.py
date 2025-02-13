# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Helpdesk Fetchmail Multicompany",
    "summary": "Adds the option to select helpdesk team and company in incoming mail server in multicompany setup.",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "category": "After-Sales",
    "author": "Onestein BV",
    "website": "https://www.onestein.eu",
    "depends": ["helpdesk_mgmt"],
    "data": [
        "security/mail_security.xml",
        "views/fetchmail_server_view.xml",
        "views/helpdesk_ticket_team_view.xml",
    ],
    "installable": True,
}
