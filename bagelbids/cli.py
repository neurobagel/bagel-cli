import click


@click.command()
@click.argument("name")
def main(name):
    click.echo(f"Bagels are good for you, {name}!")
