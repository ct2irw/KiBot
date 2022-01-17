# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from .gs import GS
from .macros import macros, document  # noqa: F401
from .pre_filters import FiltersOptions
from .log import get_logger, set_filters
from .misc import W_MUSTBEINT
from .kicad.sexpdata import load, SExpData, sexp_iter, Symbol


class Globals(FiltersOptions):
    """ Global options """
    def __init__(self):
        super().__init__()
        with document:
            self.output = ''
            """ Default pattern for output file names """
            self.dir = ''
            """ Default pattern for the output directories """
            self.out_dir = ''
            """ Base output dir, same as command line `--out-dir` """
            self.variant = ''
            """ Default variant to apply to all outputs """
            self.kiauto_wait_start = 0
            """ Time to wait for KiCad in KiAuto operations """
            self.kiauto_time_out_scale = 0.0
            """ Time-out multiplier for KiAuto operations """
            self.date_time_format = '%Y-%m-%d_%H-%M-%S'
            """ Format used for the PCB and schematic date when using the file timestamp. Uses the `strftime` format """
            self.date_format = '%Y-%m-%d'
            """ Format used for the day we started the script.
                Is also used for the PCB/SCH date formatting when `time_reformat` is enabled (default behavior).
                Uses the `strftime` format """
            self.time_format = '%H-%M-%S'
            """ Format used for the time we started the script. Uses the `strftime` format """
            self.time_reformat = True
            """ Tries to reformat the PCB/SCH date using the `date_format`.
                This assumes you let KiCad fill this value and hence the time is in ISO format (YY-MM-DD) """
            self.pcb_material = 'FR4'
            """ PCB core material. Currently used for documentation and to choose default colors.
                Currently known are FR1 to FR5 """
            self.solder_mask_color = 'green'
            """ Color for the solder mask. Currently used for documentation and to choose default colors.
                Currently known are green, black, white, yellow, purple, blue and red """
            self.silk_screen_color = 'white'
            """ Color for the markings. Currently used for documentation and to choose default colors.
                Currently known are black and white """
            self.pcb_finish = 'HAL'
            """ Finishing used to protect pads. Currently used for documentation and to choose default colors.
                KiCad 6: you should set this in the Board Setup -> Board Finish -> Copper Finish option.
                Currently known are None, HAL, HASL, HAL SnPb, HAL lead-free, ENIG, ENEPIG, Hard gold, ImAg, Immersion Silver,
                Immersion Ag, ImAu, Immersion Gold, Immersion Au, Immersion Tin, Immersion Nickel, OSP and HT_OSP """
            self.edge_connector = 'no'
            """ [yes,no,bevelled] Has the PCB edge connectors?
                KiCad 6: you should set this in the Board Setup -> Board Finish -> Edge card connectors """
            self.castellated_pads = False
            """ Has the PCB castelletad pads?
                KiCad 6: you should set this in the Board Setup -> Board Finish -> Has castellated pads """
            self.edge_plating = False
            """ Has the PCB a plated board edge?
                KiCad 6: you should set this in the Board Setup -> Board Finish -> Plated board edge """
            self.copper_finish = None
            """ {pcb_finish} """
        self.set_doc('filters', " [list(dict)] KiBot warnings to be ignored ")
        self._filter_what = 'KiBot warnings'
        self._unkown_is_error = True
        self._error_context = 'global '

    def set_global(self, opt):
        current = getattr(GS, 'global_'+opt)
        new_val = getattr(self, opt)
        if current is not None:
            logger.info('Using command line value `{}` for global option `{}`'.format(current, opt))
            return current
        if new_val:
            return new_val
        return current

    def get_stack_up(self):
        logger.debug("Looking for stack-up information in the PCB")
        pcb = None
        with open(GS.pcb_file, 'rt') as fh:
            try:
                pcb = load(fh)
            except SExpData as e:
                # Don't make it an error, will be detected and reported latter
                logger.debug("- Failed to load the PCB "+str(e))
        if pcb is None:
            return
        iter = sexp_iter(pcb, 'kicad_pcb/setup/stackup')
        if iter is None:
            return
        sp = next(iter, None)
        if sp is None:
            return
        logger.debug("- Found stack-up information")
        for e in sp[1:]:
            if isinstance(e, list) and isinstance(e[0], Symbol):
                name = e[0].value()
                value = None
                if len(e) > 1:
                    if isinstance(e[1], Symbol):
                        value = e[1].value()
                    else:
                        value = str(e[1])
                if name == 'copper_finish':
                    self.pcb_finish = value
                    logger.debug("- Copper finish: "+self.pcb_finish)
                elif name == 'edge_connector':
                    self.edge_connector = value
                    logger.debug("- Edge connector: "+self.edge_connector)
                elif name == 'castellated_pads':
                    self.castellated_pads = value == 'yes'
                    logger.debug("- Castellated pads: "+value)
                elif name == 'edge_plating':
                    self.edge_plating = value == 'yes'
                    logger.debug("- Edge plating: "+value)

    def config(self, parent):
        if GS.ki6() and GS.pcb_file and os.path.isfile(GS.pcb_file):
            self.get_stack_up()
        super().config(parent)
        # Transfer options to the GS globals
        for option in filter(lambda x: x[0] != '_', self.__dict__.keys()):
            gl = 'global_'+option
            if hasattr(GS, gl):
                setattr(GS, gl, self.set_global(option))
        # Special cases
        if not GS.out_dir_in_cmd_line and self.out_dir:
            GS.out_dir = os.path.join(os.getcwd(), self.out_dir)
        if GS.global_kiauto_wait_start and int(GS.global_kiauto_wait_start) != GS.global_kiauto_wait_start:
            GS.global_kiauto_wait_start = int(GS.global_kiauto_wait_start)
            logger.warning(W_MUSTBEINT+'kiauto_wait_start must be integer, truncating to '+str(GS.global_kiauto_wait_start))
        set_filters(self.unparsed)


logger = get_logger(__name__)
GS.global_opts_class = Globals
