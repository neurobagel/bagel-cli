from collections import namedtuple
from functools import cached_property
from pathlib import Path

from bagel.logger import logger
from bagel.utilities import file_utils
from bagel.utilities.exceptions import BagelResourceError

DEFAULT_CONFIG = "Neurobagel"

# NOTE: Even though we now support loading of custom namespaces from community configs,
# we cannot remove these hardcoded namespaces yet as they are currently tied to handling logic for specific standardized variables.
# This should be addressed as part of https://github.com/neurobagel/bagel-cli/issues/497.
Namespace = namedtuple("Namespace", ["pf", "url"])
# NOTE: We are keeping the cogatlas namespace for now to warn about its deprecation.
# Remove once we officially support custom vocabularies/namespaces.
COGATLAS = Namespace("cogatlas", "https://www.cognitiveatlas.org/task/id/")
NB = Namespace("nb", "http://neurobagel.org/vocab/")
NCIT = Namespace("ncit", "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#")
NP = Namespace(
    "np", "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/"
)

# Keep deprecated namespaces for informative user messages
DEPRECATED_NAMESPACES = [COGATLAS]
DEPRECATED_NAMESPACE_PREFIXES = [ns.pf for ns in DEPRECATED_NAMESPACES]

NEUROBAGEL = {
    "participant": NB.pf + ":ParticipantID",
    "session": NB.pf + ":SessionID",
    "sex": NB.pf + ":Sex",
    "age": NB.pf + ":Age",
    "diagnosis": NB.pf + ":Diagnosis",
    "subject_group": NB.pf + ":SubjectGroup",
    "assessment_tool": NB.pf + ":Assessment",
}

# TODO: Use importlib.resources.files(bagel) to get the path to the pipeline-catalog instead?
PROCESSING_PIPELINE_PATH = (
    Path(__file__).parent / "pipeline-catalog/processing/processing.json"
)
PROCESSING_PIPELINE_URL = "https://raw.githubusercontent.com/nipoppy/pipeline-catalog/refs/heads/main/processing/processing.json"
CONFIG_NAMESPACES_PATH = (
    Path(__file__).parent
    / "communities/config_metadata/config_namespace_map.json"
)
CONFIG_NAMESPACES_URL = "https://raw.githubusercontent.com/neurobagel/communities/refs/heads/main/config_metadata/config_namespace_map.json"

CONFIG_NAMESPACES_MAPPING, CONFIG_NAMESPACES_FETCHING_ERR = (
    file_utils.request_file(
        url=CONFIG_NAMESPACES_URL, backup_path=CONFIG_NAMESPACES_PATH
    )
)


class PipelineCatalog:
    @cached_property
    def content(self) -> list:
        """
        Fetch the pipeline catalog from the remote source and return the content.
        """
        pipeline_catalog, fetch_error = file_utils.request_file(
            url=PROCESSING_PIPELINE_URL, backup_path=PROCESSING_PIPELINE_PATH
        )
        if not pipeline_catalog:
            raise BagelResourceError(
                f"Failed to load the pipeline catalog. Error: {fetch_error} "
                "Please check that you have an internet connection and try again, or open an issue in https://github.com/neurobagel/bagel-cli/issues if the problem persists.",
            )
        if fetch_error:
            logger.warning(
                f"Failed to fetch pipeline catalog from {PROCESSING_PIPELINE_URL}. Error: {fetch_error}. "
                "Using a packaged backup pipeline catalog instead *which may be outdated*. "
                "Check your internet connection?"
            )
        return pipeline_catalog


PIPELINE_CATALOG = PipelineCatalog()
