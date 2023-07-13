from demo.app import create_app, db
from flask.cli import FlaskGroup

app = create_app()
cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command("drop_db")
def drop_db():
    db.drop_all()
    db.session.commit()


if __name__ == "__main__":
    cli()
