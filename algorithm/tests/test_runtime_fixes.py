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


class RuntimeRegressionTests(unittest.TestCase):
    def setUp(self):
        self.matrix = np.full((3, 3), 500.0)
        np.fill_diagonal(self.matrix, 0.0)
        self.old_mandatory = const.MANDATORY_DELIVERY_WINDOW
        const.MANDATORY_DELIVERY_WINDOW = True
        np.random.seed(42)

    def tearDown(self):
        const.MANDATORY_DELIVERY_WINDOW = self.old_mandatory

    def drone(self, mass=1):
        return Uav(1e7, mass, 4, costMatrix=self.matrix, startPositionId=0)

    def test_distinct_uav_types_do_not_share_cached_energy(self):
        task = Task(0, 1, 10000, 0.5)
        small, large = self.drone(1), self.drone(4)
        small.reset()
        large.reset()
        small.setCurrentTask(task)
        large.setCurrentTask(task)
        self.assertNotEqual(small.taskEnergy(task), large.taskEnergy(task))
        self.assertIsNot(small.trajectCache, large.trajectCache)

    def test_simulated_lookahead_does_not_mutate_real_uav(self):
        drone = self.drone()
        drone.reset()
        self.assertTrue(drone.canTakeTasks([Task(0, 1, 10000, 0.5), ChargingPoint(2)]))
        self.assertEqual(drone.timeSpentPerTask, [])
        self.assertEqual(drone.positionId, 0)
        self.assertEqual(drone.currentBatteryCapacity, drone.batteryCapacity)

    def test_idle_uav_is_valid_and_score_matches(self):
        ga = GeneticAlgo(Environement([self.drone(), self.drone()],
                         [Task(0, 1, 10000, 0.5), Task(1, 0, 10000, 0.5)],
                         [ChargingPoint(2)]), printGraph=False)
        chromosome = ga.addChargingTasks(Chromosome([0, 1], [0, 2]))
        self.assertNotEqual(chromosome, -1)
        ga.saveEnergiesAndTimeIn(chromosome)
        ga.solution = Individual(chromosome, ga.individualEvaluation(chromosome))
        result = check_schedule(ga)
        self.assertTrue(result['valid'], result['errors'])

    def test_impossible_deadline_is_rejected(self):
        drone = self.drone()
        drone.reset()
        drone.setCurrentTask(Task(0, 1, 0.1, 0.5))
        self.assertEqual(drone.taskEnergy(drone.currentTask), -1)

    def test_insufficient_battery_is_rejected(self):
        drone = self.drone()
        drone.reset()
        drone.currentBatteryCapacity = 1.0
        drone.setCurrentTask(Task(0, 1, 10000, 0.5))
        self.assertEqual(drone.taskEnergy(drone.currentTask), -1)

    def test_mutation_preserves_parent_and_complete_task_set(self):
        ga = GeneticAlgo(Environement([self.drone(), self.drone()],
                         [Task(0, 1, 10000, 0.5) for _ in range(5)],
                         [ChargingPoint(2)]), printGraph=False)
        parent = Chromosome(np.arange(5), np.array([2, 5]))
        children = ga.groupMutation([Individual(parent, 100)])
        self.assertEqual(len(children), 8)
        np.testing.assert_array_equal(parent.getTasksOrder(), np.arange(5))
        for child in children:
            self.assertEqual(sorted(child.getChromosome().getTasksOrder()), list(range(5)))


if __name__ == '__main__':
    unittest.main()
