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

"""This file contains class for Learning Quantities about Thoth."""

import logging
import os
import datetime

import numpy as np
import pandas as pd

from typing import Dict, List, Any

from thoth.slo_reporter.sli_base import SLIBase
from thoth.slo_reporter.sli_template import HTMLTemplates
from thoth.slo_reporter.configuration import Configuration
from thoth.slo_reporter.utils import retrieve_thoth_sli_from_ceph, evaluate_change

_LOGGER = logging.getLogger(__name__)

_REGISTERED_LEARNING_MEASUREMENT_UNIT = {
    "average_learning_rate": {"name": "Solved Learning Rate", "measurement_unit": "packages/hour"},
    "solved_packages": {"name": "Total number of solved packages", "measurement_unit": "packages"},
    "solvers": {"name": "Number of Solvers", "measurement_unit": ""},
    "average_si_learning_rate": {"name": "Security Learning Rate", "measurement_unit": "packages/hour"},
    "si_analyzed_packages": {"name": "Total number of SI analyzed packages", "measurement_unit": "packages"},
}

_LEARNING_RATE_INTERVAL = f"{int(os.getenv('LEARNING_RATE_INTERVAL', 1))}h"


class SLILearning(SLIBase):
    """This class contains functions for Learning Rate SLI."""

    _SLI_NAME = "learning"

    sli_columns = [c for c in _REGISTERED_LEARNING_MEASUREMENT_UNIT]

    def __init__(self, configuration: Configuration):
        """Initialize SLI class."""
        self.configuration = configuration
        self.total_columns = self.default_columns + self.sli_columns

    def _query_sli(self) -> List[str]:
        """Aggregate queries for learning quantities SLI Report."""
        query_labels = (
            f'{{instance="{self.configuration.instance}", job="Thoth Metrics"}}'
        )

        return {
            "average_learning_rate": {
                "query": f"increase(\
                    thoth_graphdb_unsolved_python_package_versions_change_total{query_labels}[{_LEARNING_RATE_INTERVAL}]\
                        )",
                "requires_range": True,
                "type": "average",
            },
            "solved_packages": {
                "query": f"sum(thoth_graphdb_total_number_solved_python_packages{query_labels})",
                "requires_range": True,
                "type": "latest",
            },
            "solvers": {
                "query": f"thoth_graphdb_total_number_solvers{query_labels}",
                "requires_range": True,
                "type": "latest",
            },
            "average_si_learning_rate": {
                "query": f"increase(\
                    thoth_graphdb_si_unanalyzed_python_package_versions_change_total{query_labels}[{_LEARNING_RATE_INTERVAL}]\
                        )",
                "requires_range": True,
                "type": "average",
            },
            "si_analyzed_packages": {
                "query": f"thoth_graphdb_total_number_si_analyzed_python_packages{query_labels}",
                "requires_range": True,
                "type": "latest",
            },
        }

    def _evaluate_sli(self, sli: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate SLI for report for learning quantities SLI.

        @param sli: It's a dict of SLI associated with the SLI type.
        """
        html_inputs = {}

        for learning_quantity in _REGISTERED_LEARNING_MEASUREMENT_UNIT.keys():

            learning_quantity_data = _REGISTERED_LEARNING_MEASUREMENT_UNIT[learning_quantity]
            html_inputs[learning_quantity] = {}

            if sli[learning_quantity] != "ErrorMetricRetrieval":

                # if quantity uses delta
                if learning_quantity == "solved_packages" or learning_quantity == "si_analyzed_packages":
                    html_inputs[learning_quantity]["value"] = int(sli[learning_quantity])
                else:
                    html_inputs[learning_quantity]["value"] = abs(int(sli[learning_quantity]))
            else:
                html_inputs[learning_quantity]["value"] = np.nan

            html_inputs[learning_quantity]["name"] = learning_quantity_data["name"]
            html_inputs[learning_quantity]["measurement_unit"] = learning_quantity_data["measurement_unit"]

        return html_inputs

    def _report_sli(self, sli: Dict[str, Any]) -> str:
        """Create report for learning quantities SLI.

        @param sli: It's a dict of SLI associated with the SLI type.
        """
        html_inputs = self._evaluate_sli(sli=sli)

        last_week_data = pd.DataFrame()

        if not self.configuration.dry_run:
            sli_path = f"{self._SLI_NAME}/{self._SLI_NAME}-{self.configuration.last_week_time}.csv"
            last_week_data = retrieve_thoth_sli_from_ceph(self.configuration.ceph_sli, sli_path, self.total_columns)

        for c in self.sli_columns:
            if not last_week_data.empty:
                old_value = last_week_data[c].values[0]
                change = evaluate_change(old_value=old_value, new_value=html_inputs[c]["value"])
                html_inputs[c]["change"] = change
            else:
                html_inputs[c]["change"] = "N/A"

        report = HTMLTemplates.thoth_learning_template(html_inputs=html_inputs)
        return report

    def _create_inputs_for_df_sli(
        self, sli: Dict[str, Any], datetime: datetime.datetime, timestamp: datetime.datetime,
    ) -> Dict[str, Any]:
        """Create inputs for SLI dataframe to be stored.

        @param sli: It's a dict of SLI associated with the SLI type.
        """
        parameters = locals()
        parameters.pop("self")

        output = self._create_default_inputs_for_df_sli(**parameters)

        return output
