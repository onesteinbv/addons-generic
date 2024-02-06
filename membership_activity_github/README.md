# Installation

```
pip3 install PyGithub==1.59.0
```

# Configure

1. Create a personal access token in GitHub here https://github.com/settings/tokens;
2. go to System Parameters in Odoo and copy/paste the token in `membership_activity_github.access_token`;
3. go to Projects;
4. on the project form set `Github Fullname` e.g. `odoo/odoo`
5. on member / partner form set `Github Username` e.g. `tarteo`.

# Usage

Activity will be imported every day, or you can manually run the scheduled action (Membership: Import GitHub activity)

If you imported GitHub activity but some members were not configured correctly you can re-reconcile activity to members
by going to the tree view of membership activities, select the activities you want to reconcile, and click
`Reconcile Activity with Members` in the action menu. Note that Odoo will say it selected all records but
this will not be the case as the max is 20k records.
