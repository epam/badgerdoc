import os
from typing import Union

from indigo import Indigo
from indigo.renderer import IndigoRenderer

from assets import exceptions, logger

SUPPORTED_FORMATS = {
    ".pdf": "pdf",
    ".mol": "chem",
    ".sdf": "chem",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".txt": "text",
}

logger_ = logger.get_logger(__name__)

MAX_MOLECULES_COUNT_IN_FILE = os.getenv("MAX_MOLECULES_COUNT_IN_FILE", 50)


def get_page_count(file: bytes, ext: str) -> int:
    indigo = Indigo()
    pages: int = 1
    if ext == ".sdf":
        for pages, _ in enumerate(
            indigo.iterateSDF(indigo.loadBuffer(file)), start=1
        ):
            if pages > MAX_MOLECULES_COUNT_IN_FILE:
                # Should we move this check into Pydantic?
                raise exceptions.AssetsMaxMoleculesCountExceeded(
                    "Too many molecules in file, max value: %s",
                    MAX_MOLECULES_COUNT_IN_FILE,
                )
        logger_.debug("Count of elements in file: %s", pages)
        return pages
    return pages


def __load_molecule(file: bytes, indigo: Indigo, ext: str) -> Indigo:
    # in case of .sdf (maybe others types) get only first compound for preview
    if ext == ".sdf":
        for mol in indigo.iterateSDF(indigo.loadBuffer(file)):
            return mol  # getting first element to preview
    return indigo.loadMolecule(file.decode(encoding="utf-8"))


def make_thumbnail(file: bytes, ext: str) -> Union[bool, bytes]:
    logger_.debug("Generating thumbnail from molecules")
    indigo = Indigo()  # todo: move creation of this object upper
    renderer = IndigoRenderer(indigo)
    mol = __load_molecule(file, indigo, ext)
    indigo.setOption("render-output-format", "png")
    # todo: pass as argument from front-end
    indigo.setOption("render-image-width", 1024)
    indigo.setOption("render-coloring", True)
    mol.layout()
    return renderer.renderToBuffer(mol)
