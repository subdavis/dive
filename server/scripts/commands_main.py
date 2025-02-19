"""
Cli tools for using parts of the DIVE codebase outside a web server environment
"""
import functools
import json
from typing import BinaryIO, Dict, List, Optional, TextIO

import click

from dive_utils import models, strNumericCompare
from dive_utils.serializers import kwcoco, meva, viame
from scripts import cli


@cli.command(name='verify-dive-json', help="Verify a DIVE json schema file for correctness")
@click.argument('input', type=click.File('rt'))
def verify_dive_json(input: TextIO):
    trackdicts: Dict[str, dict] = json.load(input)
    for t in trackdicts.values():
        models.Track(**t)
    click.secho('success', fg='green')


@cli.group(name="convert")
@click.version_option()
def convert():
    pass


@convert.command(name="kpf2dive")
@click.argument('inputs', type=click.File('rb'), nargs=-1)
@click.option('--output', type=click.File('wt'), default='result.json')
def convert_kpf(inputs: List[BinaryIO], output: TextIO):
    def read_in_chunks(file_object: BinaryIO, chunk_size=524288):
        """
        Lazy function (generator) to read a file piece by piece.
        """
        while True:
            data = file_object.read(chunk_size)
            if not data:
                break
            yield data

    tracks = meva.load_kpf_as_tracks([read_in_chunks(file) for file in inputs])
    json.dump(tracks, output)
    click.secho(f'wrote output {output.name}', fg='green')


@convert.command(name="coco2dive")
@click.argument('input', type=click.File('rt'))
@click.option('--output', type=click.File('wt'), default='result.json')
@click.option('--output-attrs', type=click.File('wt'), default='attributes.json')
def convert_coco(input: TextIO, output: TextIO, output_attrs: TextIO):
    coco_json = json.load(input)
    tracks, attributes = kwcoco.load_coco_as_tracks_and_attributes(coco_json)
    json.dump(tracks, output)
    json.dump(attributes, output_attrs, indent=4)
    click.secho(f'wrote output {output.name}', fg='green')
    click.secho(f'wrote attrib {output_attrs.name}', fg='green')


@convert.command(name="viame2dive")
@click.argument('input', type=click.File('rt'))
@click.option('--output', type=click.File('wt'), default='result.json')
@click.option('--output-attrs', type=click.File('wt'), default='attributes.json')
def convert_viame_csv(input: TextIO, output: TextIO, output_attrs: TextIO):
    rows = input.readlines()
    tracks, attributes = viame.load_csv_as_tracks_and_attributes(rows)
    json.dump(tracks, output)
    json.dump(attributes, output_attrs, indent=4)
    click.secho(f'wrote output {output.name}', fg='green')
    click.secho(f'wrote attrib {output_attrs.name}', fg='green')


@convert.command(name="dive2viame")
@click.argument('input', type=click.File('rt'))
@click.option(
    '--meta',
    type=click.File('rt'),
    default=None,
    help="Populate image list and fps from meta.json",
)
@click.option('--output', type=click.File('wt'), default='result.csv')
@click.option(
    '--exclude-below',
    type=click.FloatRange(0, 1),
    default=0,
    help="Exclude tracks below confidence value",
)
@click.option('--fps', type=click.FloatRange(0), default=None, help="Annotation FPS")
def convert_dive_json(
    input: TextIO,
    meta: Optional[TextIO],
    output: TextIO,
    exclude_below: float,
    fps: Optional[float],
):
    data = json.load(input)
    imagelist = []
    if meta:
        metadata = json.load(meta)
        imagelist = sorted(
            metadata['originalImageFiles'],
            key=functools.cmp_to_key(strNumericCompare),
        )
        if fps is None:
            fps = metadata['fps']
    output.writelines(
        viame.export_tracks_as_csv(
            data,
            excludeBelowThreshold=True,
            thresholds={'default': exclude_below},
            filenames=imagelist,
            fps=fps,
        )
    )
    click.secho(f'wrote output {output.name}', fg='green')
