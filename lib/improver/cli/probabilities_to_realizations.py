#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2017-2019 Met Office.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
"""Script to convert from probabilities to ensemble realization data."""

from improver import cli


@cli.clizefy
@cli.with_output
def process(cube: cli.inputcube,
            raw_forecast: cli.inputcube = None,
            *,
            realizations_count: int = None,
            reorder=False,
            rebadge=False,
            random_seed: int = None,
            ignore_ecc_bounds=False):
    """Convert from probabilities to ensemble realizations.

    Args:
        cube (iris.cube.Cube):
            Cube to be processed.
        raw_forecast (iris.cube.Cube):
            Cube of raw (not post processed) weather data.
            This option is compulsory, if the reorder option is selected.
        realizations_count (int):
            Optional definition of the number of ensemble realizations to
            be generated. These are generated though an intermediate
            percentile representation. Theses percentiles will be
            distributed regularly with the aim of dividing into blocks
            of equal probability. If the reorder option is specified
            and the number of realization is not given the number
            of realizations is taken from the number of realizations
            in the raw forecast cube.
        reorder (bool):
            The option used to create ensemble realizations from percentiles
            by reordering the input percentiles based on the order of the
            raw ensemble.
        rebadge (bool):
            Th option used to create ensemble realizations from percentiles
            by rebadging the input percentiles.
        random_seed (int):
            Option to specify a value for the random seed for testing
            purposes, otherwise the default random seed behaviours is
            utilised. The random seed is used in the generation of the
            random numbers used for splitting tied values within the raw
            ensemble, so that the values from the input percentiles can
            be ordered to match the raw ensemble.
        ignore_ecc_bounds (bool):
            If True, where percentiles (calculated as an intermediate output
            before realization) exceed to ECC bounds range, raises a warning
            rather than an exception.

    Returns:
        iris.cube.Cube:
            Processed result Cube.

    Raises:
        RuntimeError:
            If rebadge is used with raw_forecast.
        RuntimeError:
            If rebadge is used with random_seed.
        RuntimeError:
            If raw_forecast isn't supplied when using reorder.
    """
    from iris.exceptions import CoordinateNotFoundError
    from improver.ensemble_copula_coupling.ensemble_copula_coupling import (
        GeneratePercentilesFromProbabilities, RebadgePercentilesAsRealizations,
        EnsembleReordering)

    if rebadge:
        if raw_forecast is not None:
            raise RuntimeError('rebadge cannot be used with raw_forecast.')
        if random_seed is not None:
            raise RuntimeError('rebadge cannot be used with random_seed.')

    if reorder:
        # If realizations_count is not given, take the number from the raw
        # ensemble cube.
        if realizations_count is None:
            if raw_forecast is None:
                message = ("You must supply a raw forecast cube if using the "
                           "reorder option.")
                raise RuntimeError(message)
            try:
                realizations_count = len(
                    raw_forecast.coord("realization").points)
            except CoordinateNotFoundError:
                raise RuntimeError('The raw forecast must have a realization '
                                   'coordinate.')

        cube = GeneratePercentilesFromProbabilities(
            ecc_bounds_warning=ignore_ecc_bounds).process(
            cube, no_of_percentiles=realizations_count)
        result = EnsembleReordering().process(
            cube, raw_forecast, random_ordering=False, random_seed=random_seed)
    elif rebadge:
        cube = GeneratePercentilesFromProbabilities(
            ecc_bounds_warning=ignore_ecc_bounds).process(
            cube, no_of_percentiles=realizations_count)
        result = RebadgePercentilesAsRealizations().process(cube)
    return result
