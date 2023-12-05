import click

from cq.check_code_quality import check_files_code_quality


@click.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def run(files):
    """Run tests for the specified files."""
    check_files_code_quality(files)


if __name__ == '__main__':
    run()
