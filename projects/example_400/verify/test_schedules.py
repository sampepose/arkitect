"""400 Oak's schedules: every door on the plans gets a mark, quantities are the plans',
   and every sleeping room has a W-A."""
import unittest

from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


class ScheduleTests(unittest.TestCase):

    def test_the_schedules_pass(self):
        from src import schedules as S
        S.check_schedules()

    def test_the_door_quantities(self):
        from src import schedules as S
        d = S.door_totals()
        self.assertEqual((d["D-1"], d["D-2"], d["D-4"], d["D-4A"], d["D-6"], d["D-7"]), (3, 1, 1, 4, 1, 1))
        self.assertEqual(sum(d.values()), sum(len(m['doors']) for m in S.B1.LEVEL.values())+2*len(S.B2.B2doors)+d["D-5"])

    def test_a_door_with_no_mark_stops_the_build(self):
        from src import schedules as S
        with self.assertRaises(ValueError):
            S._b1_mark((5.0, 10.0, 1.75, 'h', 1))

    def test_the_window_quantities_are_the_plans(self):
        from src import schedules as S
        w = S.window_totals()
        self.assertEqual(w["D"], 1)
        self.assertEqual(sum(w.values()), sum(len(m['wins']) for m in S.B1.LEVEL.values())+sum(len(S.B2.b2_wins(lv)) for lv in (1, 2)))

    def test_seven_sleeping_rooms_each_with_a_w_a(self):
        from src import schedules as S
        from src.sheets.g001 import BEDROOMS
        self.assertEqual(len(S.sleeping_rooms()), BEDROOMS)


    def test_the_plans_tag_every_door_the_schedule_counts(self):
        from collections import Counter
        from src import schedules as sc, building1 as b1
        tagged = Counter(mk for lv in b1.LEVEL for _x, _y, mk in sc.door_tags(1, lv))
        tagged.update(mk for _unit in (2, 3) for _x, _y, mk in sc.door_tags(2, 1))
        self.assertEqual(tagged, sc.door_totals())
        self.assertEqual(set(tagged), set(sc.DOORS))


if __name__ == '__main__':
    unittest.main()
