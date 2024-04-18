# Copyright 2017-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# This monkey patch allows list databases to find databases of which the current
# user is the owner, but also those that have an owner role that the current
# user is a member of.
import logging
from contextlib import closing
import odoo
from odoo.exceptions import AccessDenied
import odoo.release
import odoo.sql_db
import odoo.tools

_logger = logging.getLogger(__name__)


def list_dbs(force=False):
    if not odoo.tools.config['list_db'] and not force:
        raise odoo.exceptions.AccessDenied()

    if not odoo.tools.config['dbfilter'] and odoo.tools.config['db_name']:
        # In case --db-filter is not provided and --database is passed, Odoo will not
        # fetch the list of databases available on the postgres server and instead will
        # use the value of --database as comma seperated list of exposed databases.
        res = sorted(db.strip() for db in odoo.tools.config['db_name'].split(','))
        return res

    chosen_template = odoo.tools.config['db_template']
    templates_list = tuple(set(['postgres', chosen_template]))
    db = odoo.sql_db.db_connect('postgres')
    with closing(db.cursor()) as cr:
        try:
            # ### START OF PATCH ####
            # cr.execute(
            #     "select datname from pg_database where datdba=(select usesysid from pg_user where usename=current_user) and not datistemplate and datallowconn and datname not in %s order by datname",
            #     (templates_list,))
            cr.execute(
                """SELECT datname
                FROM pg_database 
                WHERE NOT datistemplate AND datallowconn AND datname NOT IN %s 
                    AND datdba IN 
                (
                    WITH RECURSIVE membership_tree(grpid, userid) AS (
                        -- Get all roles and list them as their own group as well
                        SELECT pg_roles.oid, pg_roles.oid
                        FROM pg_roles
                        UNION ALL
                        -- Now add all group membership
                        SELECT m_1.roleid, t_1.userid
                        FROM pg_auth_members m_1, membership_tree t_1
                        WHERE m_1.member = t_1.grpid
                    )
                    SELECT DISTINCT t.grpid
                    FROM membership_tree t, pg_roles r, pg_roles m
                    WHERE t.grpid = m.oid AND t.userid = r.oid
                    AND t.userid IN (SELECT usesysid FROM pg_user WHERE usename=current_user)
                )
                ORDER BY datname;""",
            (templates_list,)
            )
            # ### END OF PATCH ###
            res = [odoo.tools.ustr(name) for (name,) in cr.fetchall()]
        except Exception:
            _logger.exception('Listing databases failed:')
            res = []
    return res


odoo.service.db.list_dbs = list_dbs
