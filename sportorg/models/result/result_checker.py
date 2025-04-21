import logging

from sportorg.common.otime import OTime
from sportorg.models.constant import StatusComments
from sportorg.models.memory import Person, ResultStatus, race, Result, find, Split, Team, Sex
from sportorg.models.result.result_calculation import ResultCalculation


class ResultCheckerException(Exception):
    pass


class ResultChecker:
    def __init__(self, person: Person):
        self.person = person

    def check_result(self, result):
        if self.person is None:
            return True
        if self.person.group is None:
            return True

        course = race().find_course(result)

        if race().get_setting('result_processing_mode', 'time') == 'scores':
            result.check(course)
            scores = self.calculate_rogaine_scores(result)
            result.penalty_points = self.calculate_rogaine_penalty(result, scores)
            result.scores = scores - result.penalty_points
            return True

        if race().get_setting('marked_route_dont_dsq', False):
            # mode: competition without disqualification for mispunching (add penalty for missing cp)
            result.check(course)
            return True

        if course is None:
            if self.person.group.is_any_course:
                return False
            return True

        if self.person.group.is_any_course:
            return True

        return result.check(course)

    @classmethod
    def checking(cls, result):
        if result.person is None:
            raise ResultCheckerException('Not person')
        o = cls(result.person)
        if result.status in [ResultStatus.OK, ResultStatus.MISSING_PUNCH, ResultStatus.OVERTIME]:
            result.status = ResultStatus.OK

            check_flag = o.check_result(result)
            ResultChecker.calculate_penalty(result)
            if not check_flag:
                result.status = ResultStatus.MISSING_PUNCH
                if not result.status_comment:
                    result.status_comment = StatusComments().remove_hint(StatusComments().get())
            elif result.person.group and result.person.group.max_time.to_msec():
                result_time = result.get_result_otime() + result.get_credit_time() - result.get_penalty_time()
                if result_time > result.person.group.max_time:
                    if race().get_setting('result_processing_mode', 'time') == 'time':
                        result.status = ResultStatus.OVERTIME
                    elif race().get_setting('result_processing_mode', 'time') == 'scores':
                        max_delay_ms = race().get_setting('result_processing_scores_max_delay', 30)*60000
                        if result_time.to_msec() > result.person.group.max_time.to_msec() + max_delay_ms: 
                            result.status = ResultStatus.OVERTIME

        return o

    @classmethod
    def check_all(cls):
        logging.debug('Checking all results')
        for result in race().results:
            if result.person:
                ResultChecker.checking(result)

    @staticmethod
    def calculate_penalty(result):
        mode = race().get_setting('marked_route_mode', 'off')
        result.penalty_time = OTime()
        result.penalty_laps = 0
        if mode == 'off':
            return

        person = result.person

        if person is None:
            return
        if person.group is None:
            return

        course = race().find_course(result)
        if not course:
            return

        if race().get_setting('marked_route_dont_dsq', False):
            # free order, don't penalty for extra cp
            penalty = ResultChecker.penalty_calculation_free_order(result.splits, course.controls)
        else:
            # marked route with penalty
            penalty = ResultChecker.penalty_calculation(result.splits, course.controls, check_existence=True)

        if race().get_setting('marked_route_max_penalty_by_cp', False):
            # limit the penalty by quantity of controls
            penalty = min(len(course.controls), penalty)

        result.penalty_laps = 0
        result.penalty_time = OTime()

        if mode == 'laps':
            result.penalty_laps = penalty
        elif mode == 'time':
            time_for_one_penalty = OTime(msec=race().get_setting('marked_route_penalty_time', 60000))
            result.penalty_time = time_for_one_penalty * penalty

    @staticmethod
    def get_marked_route_incorrect_list(controls):
        ret = []
        for i in controls:
            code_str = str(i.code)
            if code_str and '(' in code_str:
                correct = code_str.split('(')[0].strip()
                if correct.isdigit():
                    for cp in code_str.split('(')[1].split(','):
                        cp = cp.strip(')').strip()
                        if cp != correct and cp.isdigit():
                            if cp not in ret:
                                ret.append(cp)
        return ret

    @staticmethod
    def penalty_calculation(splits, controls, check_existence=False):
        """:return quantity of incorrect or duplicated punches, order is ignored
            origin: 31,41,51; athlete: 31,41,51; result:0
            origin: 31,41,51; athlete: 31; result:0
            origin: 31,41,51; athlete: 41,31,51; result:0
            origin: 31,41,51; athlete: 31,42,51; result:1
            origin: 31,41,51; athlete: 31,41,51,52; result:1
            origin: 31,41,51; athlete: 31,42,51,52; result:2
            origin: 31,41,51; athlete: 31,31,41,51; result:1
            origin: 31,41,51; athlete: 31,41,51,51; result:1
            origin: 31,41,51; athlete: 32,42,52; result:3
            origin: 31,41,51; athlete: 31,41,51,61,71,81,91; result:4
            origin: 31,41,51; athlete: 31,41,52,61,71,81,91; result:5
            origin: 31,41,51; athlete: 51,61,71,81,91,31,41; result:4
            origin: 31,41,51; athlete: 51,61,71,81,91,32,41; result:5
            origin: 31,41,51; athlete: 51,61,71,81,91,32,42; result:6
            origin: 31,41,51; athlete: 52,61,71,81,91,32,42; result:7
            origin: 31,41,51; athlete: no punches; result:0

            with existence checking (if athlete has less punches, each missing add penalty):
            origin: 31,41,51; athlete: 31; result:2
            origin: 31,41,51; athlete: no punches; result:3

            wildcard support for free order
            origin: *,*,* athlete: 31; result:2
            origin: *,*,* athlete: 31,31; result:2
            origin: *,*,* athlete: 31,31,31,31; result:3
        """
        user_array = [i.code for i in splits]
        origin_array = [i.get_number_code() for i in controls]
        res = 0

        # In theory can return less penalty for uncleaned card / может дать 0 штрафа при мусоре в чипе
        if check_existence and len(user_array) < len(origin_array):
            # add 1 penalty score for missing points
            res = len(origin_array) - len(user_array)

        incorrect_array = ResultChecker.get_marked_route_incorrect_list(controls)

        if len(incorrect_array) > 0:
            # marked route with choice, controls like 31(31,131), penalty only wrong choice (once),
            # ignoring controls from another courses, previous punches on uncleared card, duplicates
            # this mode allows combination of marked route and classic course, but please use different controls
            for i in incorrect_array:
                if i in user_array:
                    res += 1
        else:
            # classic penalty model - count correct control punch only once, others are recognized as incorrect
            # used for orientathlon, corridor training with choice
            for i in origin_array:
                # remove correct points (only one object per loop)
                if i == '0' and len(user_array):
                    del user_array[0]

                elif i in user_array:
                    user_array.remove(i)

            # now user_array contains only incorrect and duplicated values
            res += len(user_array)

        return res

    @staticmethod
    def penalty_calculation_free_order(splits, controls):
        """:return quantity penalty, duplication checked
            origin: * ,* ,* ; athlete: 31,41,51; result:0
            origin: * ,* ,* ; athlete: 31,31,51; result:1
            origin: * ,* ,* ; athlete: 31,31,31; result:2
            origin: * ,* ,* ; athlete: 31; result:2

            support of first/last mandatory cp
            origin: 40,* ,* ,90; athlete: 40,31,32,90; result:0
            origin: 40,* ,* ,90; athlete: 40,31,40,90; result:1
            origin: 40,* ,* ,90; athlete: 40,40,40,90; result:2
            origin: 40,* ,* ,90; athlete: 40,90,90,90; result:2
            origin: 40,* ,* ,90; athlete: 31,32,33,90; result:4
            origin: 40,* ,* ,90; athlete: 31,40,31,90; result:1
            origin: 40,* ,* ,90; athlete: 31,40,90,41; result:1
            origin: 40,* ,* ,90; athlete: 31,40,31,32; result:1
            origin: 40,* ,* ,90; athlete: 31,40,31,40; result:2
            origin: 40,* ,* ,90; athlete: 40,40,90,90; result:2
            origin: 40,* ,* ,90; athlete: 40,41,90,90; result:0 TODO:1 - only one incorrect case
        """
        correct_count = 0
        for i in splits:
            if not i.has_penalty:
                correct_count += 1
        return max(len(controls) - correct_count, 0)

    @staticmethod
    def get_control_score(code):
        obj = race()
        if obj.get_setting('result_processing_score_mode', 'fixed') == 'fixed':
            return obj.get_setting('result_processing_fixed_score_value', 1.0)  # fixed score per control

        control = find(obj.control_points, code=str(code))
        if control and control.score:
            return int(control.score)

        return int(code)//10  # score = code / 10

    @staticmethod
    def calculate_rogaine_scores(result):
        user_array = []
        points = 0
        for cur_split in result.splits:
            if cur_split.is_correct:
                code = str(cur_split.code)
                if code not in user_array:
                    user_array.append(code)
                    points += ResultChecker.get_control_score(code)
        return points

    @staticmethod
    def calculate_rogaine_penalty(result, score):
        penalty_points = 0
        if result.person and result.person.group:
            user_time = result.get_result_otime()
            max_time = result.person.group.max_time
            if OTime() < max_time < user_time:
                time_diff = user_time - max_time
                seconds_diff = time_diff.to_sec()
                minutes_diff = (seconds_diff + 59) // 60  # note, 1:01 = 2 minutes
                penalty_step = race().get_setting('result_processing_scores_minute_penalty', 1.0)
                penalty_points = minutes_diff*penalty_step
        return min(penalty_points, score)

    @staticmethod
    def fix_mix_groups():
        logging.debug('Fix mixed groups')
        for result in race().results:
            p = result.person
            if p.group.sex != Sex.MF and p.group.sex != p.sex:
                old_group_name = p.group.name
                new_group_name = old_group_name.replace('-М', '-МЖ').replace('-Ж', '-МЖ')
                print('Change group for', p.name, p.surname, 'from', old_group_name, 'to', new_group_name)
                p.group = find(race().groups, name=new_group_name)
        

    @staticmethod
    def find_pursuits():
        logging.debug('Find pursuits')
        known_orders = {}
        for result in race().results:
            user_cp_order = '-'.join([i.code for i in result.splits])
            if user_cp_order not in known_orders:
                known_orders[user_cp_order] = []
            known_orders[user_cp_order].append(result)
        all_groups = []
        for cp_order,results_list in known_orders.items():
            known_groups = []
            group_dict = {}
            for result in results_list:
                if result.person is None:
                    continue
                bib = result.person.bib
                for other_result in results_list:
                    if result == other_result:
                        continue
                    if result.compare(other_result):
                        other_bib = other_result.person.bib
                        if bib in group_dict:
                            if other_bib not in group_dict[bib]:
                                group_dict[bib].append(other_bib)
                                group_dict[other_bib] = group_dict[bib]
                        elif other_bib in group_dict:
                            if bib not in group_dict[other_bib]:
                                group_dict[other_bib].append(bib)
                                group_dict[bib] = group_dict[other_bib]
                        else:
                            new_group = [bib, other_bib]
                            group_dict[bib] = new_group
                            group_dict[other_bib] = new_group
                            known_groups.append(new_group)
            if known_groups:
                all_groups += known_groups
        print(len(all_groups), all_groups)
        for g in all_groups:
            new_team = Team()
            for bib in g:
                person = find(race().persons, bib=bib)
                if person.team:
                    if person.team.name != new_team.name:
                        new_team.name += '/' if new_team.name else ''
                        new_team.name += person.team.name
                    if person.team.contact != new_team.contact:
                        new_team.contact += '/' +person.team.contact
                new_team.group = person.group
                person.team = new_team
            if not new_team.name:
                new_team.name = '-'
            race().teams.append(new_team)
            logging.debug('New team: {}'.format(new_team.name))
        ResultCalculation(race()).process_results()


