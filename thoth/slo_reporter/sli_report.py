#!/usr/bin/env python3
# slo-reporter
# Copyright(C) 2020 Francesco Murdaca
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""This file contains all sli metrics that should be included in the report."""

import os
import logging

from .configuration import Configuration

from .sli_references import _add_dashbords

from .sli_learning import SLILearning
from .sli_kebechet import SLIKebechet
from .sli_knowledge_graph import SLIKnowledgeGraph
from .sli_pypi_knowledge_graph import SLIPyPIKnowledgeGraph
from .sli_thoth_integration import SLIThothIntegrations
from .sli_user_api import SLIUserAPI
from .sli_workflow_quality import SLIWorkflowQuality
from .sli_workflow_latency import SLIWorkflowLatency

from .sli_template import HTMLTemplates


_LOGGER = logging.getLogger(__name__)


class SLIReport:
    """This class contains all sections included in a report."""

    def __init__(self, configuration: Configuration):
        """Initialize SLI Report."""
        self.configuration = configuration

        self.report_subject = (
            f"Thoth Service Level Indicators Update Day" + f" ({self.configuration.end_time.strftime('%Y-%m-%d')})"
        )
        _LOGGER.info(self.report_subject)

        self.report_start = HTMLTemplates.thoth_report_start_template()

        self.report_intro = HTMLTemplates.thoth_report_intro_template(
            html_inputs={
                "environment": self.configuration.environment,
                "start_time": str(self.configuration.start_time.strftime("%Y-%m-%d")),
                "end_time": str(self.configuration.end_time.strftime("%Y-%m-%d")),
            },
        )

        self.report_style = HTMLTemplates.thoth_report_style_template()

        self.report_sli_context = {
            SLIPyPIKnowledgeGraph._SLI_NAME: SLIPyPIKnowledgeGraph(configuration=self.configuration)._aggregate_info(),
            SLIKnowledgeGraph._SLI_NAME: SLIKnowledgeGraph(configuration=self.configuration)._aggregate_info(),
            SLILearning._SLI_NAME: SLILearning(configuration=self.configuration)._aggregate_info(),
            SLIThothIntegrations._SLI_NAME: SLIThothIntegrations(configuration=self.configuration)._aggregate_info(),
            SLIKebechet._SLI_NAME: SLIKebechet(configuration=self.configuration)._aggregate_info(),
            SLIUserAPI._SLI_NAME: SLIUserAPI(configuration=self.configuration)._aggregate_info(),
            # SLIWorkflowQuality._SLI_NAME: SLIWorkflowQuality(configuration=self.configuration)._aggregate_info(),
            # SLIWorkflowLatency._SLI_NAME: SLIWorkflowLatency(configuration=self.configuration)._aggregate_info(),
        }

        self.report_references = _add_dashbords(configuration=configuration)

        self.report_end = HTMLTemplates.thoth_report_end_template()
