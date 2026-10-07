"""Inspect scenario inputs without starting a GA or Monte Carlo campaign."""
import json
import argparse
from pathlib import Path
import runpy
from scipy.io import whosmat
from GeneticAlgo import GeneticAlgo
import monteCarloRunScenario as mc
from Uav import Uav

parser = argparse.ArgumentParser()
parser.add_argument('--profile', choices=['repo', 'chapter5'], default='repo')
parser.add_argument('--output', default='results/inputs.json')
args = parser.parse_args()
if args.profile == 'chapter5':
    original_init = Uav.__init__
    def chapter5_init(self, *positional, **kwargs):
        kwargs['cd'] = 0.3
        original_init(self, *positional, **kwargs)
    Uav.__init__ = chapter5_init

captured = []
GeneticAlgo.run = lambda ga: captured.append((ga.uavs, ga.tasks, ga.chargingPoints))
mc.monteCarloRun = lambda env, printGraph: captured.append(
    (env.getUavs(), env.getTasks(), env.getChargingPoints()))
reports = {}
for name, script in [('simple', 'simpleScenario.py'), ('A', 'complexScenarioA.py'), ('B', 'complexScenarioB.py')]:
    runpy.run_path(script, run_name='__main__')
    uavs, tasks, charging = captured[-1]
    impossible = []
    for j, task in enumerate(tasks):
        bounds = [float((u.costMatrix[u.startPositionId, task.startPositionId]
                         + u.costMatrix[task.startPositionId, task.endPositionId]) / u.maxVelocity)
                  for u in uavs if task.packageMass <= u.maxPayloadMass]
        if bounds and min(bounds) > task.maxDeliveryWindow + 1e-5:
            impossible.append({'task': j, 'deadline_s': task.maxDeliveryWindow,
                               'earliest_direct_completion_lower_bound_s': min(bounds)})
    reports[name] = {'uavs': len(uavs), 'tasks': len(tasks), 'charging_points': len(charging),
                     'fleet': [{'mass_kg':u.mass, 'max_payload_kg':u.maxPayloadMass,
                                'Ar_m2':u.Ar, 'Ad_m2':u.Ad, 'max_velocity_m_s':u.maxVelocity,
                                'battery_mj':u.batteryCapacity/1e6, 'cd':u.cd,
                                'Fm':u.Fm, 'eta':u.eta, 'rho':u.rho} for u in uavs],
                     'matrix_shapes': [list(u.costMatrix.shape) for u in uavs],
                     'deadline_min_s': min(t.maxDeliveryWindow for t in tasks),
                     'deadline_max_s': max(t.maxDeliveryWindow for t in tasks),
                     'direct_first_task_deadline_violations': impossible,
                     'note': 'These direct-path bounds assume metric path distances; they are not a general infeasibility proof.'}
reports['mat_files'] = {p.name: whosmat(p) for p in Path('distancesCostMatrix').glob('*.mat')}
Path(args.output).write_text(json.dumps(reports, indent=2), encoding='utf-8')
print(json.dumps(reports, indent=2))
