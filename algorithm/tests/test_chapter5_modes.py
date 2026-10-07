import unittest
import numpy as np
from AlgoConstants import AlgoConstants as const
from ChargingPoint import ChargingPoint
from Chromosome import Chromosome
from Environement import Environement
from GeneticAlgo import GeneticAlgo
from Individual import Individual
from Task import Task
from Uav import Uav
from run_scenarios import check_schedule


class Chapter5ModeTests(unittest.TestCase):
    def setUp(self):
        self.old_flags = const.MANDATORY_DELIVERY_WINDOW, const.RC_ONLY_END
        self.matrix = np.full((3, 3), 500.0)
        np.fill_diagonal(self.matrix, 0.0)

    def tearDown(self):
        const.MANDATORY_DELIVERY_WINDOW, const.RC_ONLY_END = self.old_flags

    def ga(self, tasks):
        drone = Uav(1e7, 1, 4, costMatrix=self.matrix)
        return GeneticAlgo(Environement([drone], tasks, [ChargingPoint(2)]), printGraph=False)

    def test_v3_discards_infeasible_task_before_selection(self):
        const.MANDATORY_DELIVERY_WINDOW, const.RC_ONLY_END = True, True
        ga = self.ga([Task(0, 1, 0.1, 0.5)])
        ga.population = np.array([Individual(Chromosome(np.array([0]), np.array([1])))], dtype=object)
        ga.oppositePopulation = np.array([], dtype=object)
        ga.addChargingTasksAndEvaluationPopulations()
        self.assertEqual(len(ga.population), 0)

    def test_soft_deadline_uses_delivery_fraction_and_valid_score(self):
        const.MANDATORY_DELIVERY_WINDOW, const.RC_ONLY_END = False, True
        ga = self.ga([Task(0, 1, 0.1, 0.5), Task(1, 0, 10000, 0.5)])
        result = ga.addChargingTasksIndividual(Individual(Chromosome(np.array([0, 1]), np.array([2]))))
        ga.solution = result
        validation = check_schedule(ga)
        self.assertTrue(validation['valid'], validation['errors'])
        self.assertEqual(validation['on_time_fraction'], 0.5)
        self.assertAlmostEqual(validation['score'], 2 * validation['energy_j'], places=5)

    def test_v3_final_schedule_is_checked_after_recharge_insertion(self):
        const.MANDATORY_DELIVERY_WINDOW, const.RC_ONLY_END = True, True
        ga = self.ga([Task(0, 1, 10000, 0.5), Task(1, 0, 10000, 0.5)])
        result = ga.addChargingTasksIndividual(Individual(Chromosome(np.array([0, 1]), np.array([2]))))
        ga.solution = result
        validation = check_schedule(ga)
        self.assertTrue(validation['valid'], validation['errors'])
        self.assertEqual(validation['on_time_fraction'], 1.0)


if __name__ == '__main__':
    unittest.main()
