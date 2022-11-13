import platform

from sportorg import config
from sportorg.common.template import get_text_from_file
from sportorg.models.memory import race, Team
from sportorg.modules.configs.configs import Config
from sportorg.modules.printing.printout_split import SportorgPrinter

from sportorg.modules.printing.printing import print_html
from sportorg.config import template_dir
from sportorg.models.result.split_calculation import GroupSplits

from sportorg.language import _

class NoResultToPrintException(Exception):
    pass


class NoPrinterSelectedException(Exception):
    pass


def split_printout(result):
    person = result.person

    if not person or not person.group:
        raise NoResultToPrintException('No results to print')

    obj = race()
    course = obj.find_course(result)
    if not course:
        print('Unknown course for result with bib', result.bib)

    if person.group and course:
        printer = Config().printer.get('split')
        template_path = obj.get_setting('split_template', template_dir('split', '1_split_printout.html'))

        s = GroupSplits(obj, person.group).generate(True)
        if not obj.is_team_race() and obj.get_setting('system_start_source') == 'protocol':
            result.check_who_can_win()

        if not str(template_path).endswith('.html') and platform.system() == 'Windows':
            # Internal split printout, pure python. Works faster, than jinja2 template + pdf

            size = 60  # base scale factor is 60, used win32con.MM_TWIPS MapMode (unit = 1/20 of dot, 72dpi)

            array = str(template_path).split(_('scale') + '=')
            if len(array) > 1:
                scale = array[1]
                if scale.isdecimal():
                    size = int(scale) * size // 100

            pr = SportorgPrinter(printer,
                            size,
                            int(obj.get_setting('print_margin_left', 5.0)),
                            int(obj.get_setting('print_margin_top', 5.0)))

            pr.print_split(result)
            pr.end_doc()

            return

        team = person.team
        if not team:
            team = Team()

        template = get_text_from_file(
            template_path,
            race=obj.to_dict(),
            person=person.to_dict(),
            result=result.to_dict(),
            group=person.group.to_dict(),
            course=course.to_dict(),
            team=team.to_dict(),
            items=s.to_dict()
        )
        if not config.DEBUG and not printer:
            raise NoPrinterSelectedException('No printer selected')
        print_html(
            printer,
            template,
            obj.get_setting('print_margin_left', 5.0),
            obj.get_setting('print_margin_top', 5.0),
            obj.get_setting('print_margin_right', 5.0),
            obj.get_setting('print_margin_bottom', 5.0),
            obj.get_setting('print_scale', 100),
        )
