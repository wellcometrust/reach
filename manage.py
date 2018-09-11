import click
from models import DatabaseEngine


@click.group()
def cli():
    pass


@click.command()
def recreate_db():
    db = DatabaseEngine()

    click.echo('Dropping current state DB...')
    db.meta.drop_all()

    click.echo('Recreating...')
    db.meta.create_all()
    db.session.commit()
    click.echo('Done')


@click.command()
@click.option('--model_file', help='The full path to a pkl model file. Optionnal')
@click.option('--vectorizer_file', help='The full path to a pkl vectorizer file. Optionnal')
@click.argument('scraper_file', type=click.Path(exists=True))
@click.argument('references_file', type=click.Path(exists=True))
def run_predict(scraper_file, references_file,
                model_file, vectorizer_file):
    pass


cli.add_command(recreate_db)
cli.add_command(run_predict)

if __name__ == '__main__':
    cli()
