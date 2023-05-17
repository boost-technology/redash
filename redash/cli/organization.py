from click import argument
from flask.cli import AppGroup

from redash import models

manager = AppGroup(help="Organization management commands.")


@manager.command()
@argument("domains")
def set_oauth_domains(domains):
    """
    Sets the allowable domains to the comma separated list DOMAINS.
    """
    organization = models.Organization.query.first()
    k = models.Organization.SETTING_OAUTH_DOMAINS
    organization.settings[k] = domains.split(",")
    models.db.session.add(organization)
    models.db.session.commit()
    print(
        "Updated list of allowed domains to: {}".format(
            organization.oauth_domains
        )
    )


@manager.command()
def show_oauth_domains():
    organization = models.Organization.query.first()
    print(
        "Current list of OAuth domains: {}".format(
            ", ".join(organization.oauth_domains)
        )
    )


@manager.command(name="list")
def list_command():
    """List all organizations"""
    orgs = models.Organization.query
    for i, org in enumerate(orgs.order_by(models.Organization.name)):
        if i > 0:
            print("-" * 20)

        print("Id: {}\nName: {}\nSlug: {}".format(org.id, org.name, org.slug))
