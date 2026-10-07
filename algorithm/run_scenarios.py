"""Run the project's scenario scripts headlessly and validate every returned schedule."""
import argparse
from collections import Counter
import contextlib
import hashlib
import json
import math
from pathlib import Path
import random
import runpy
import time
import traceback

import matplotlib.pyplot as plt
import numpy as np
import scipy

from AlgoConstants import AlgoConstants as const
from GeneticAlgo import GeneticAlgo
from Uav import Uav
from Positions import Positions


SCENARIOS = {
    "simple": "simpleScenario.py",
    "A": "complexScenarioA.py",
    "B": "complexScenarioB.py",
}


def check_schedule(ga):
    """Recompute constraints/energy from input matrices and recorded step durations.

    Does not call the GA's feasibility or objective functions. This is a consistency
    checker, not a global optimality certificate or verification of the risk planner.
    """
    chromosome = ga.getSolution().getChromosome()
    routes = chromosome.getTasksPerUav()
    times = chromosome.getTimePerTaskPerUav()
    energies = chromosome.getEnergyPerTaskPerUav()
    errors, rows, delivery_ids, totals = [], [], [], []
    on_time = 0
    for u, route in enumerate(routes):
        drone = ga.uavs[u]
        position, elapsed, battery = drone.startPositionId, 0.0, drone.batteryCapacity
        total = 0.0
        if len(route) != len(times[u]) or len(route) != len(energies[u]):
            errors.append(f"UAV {u}: route/time/energy lengths differ")
            continue
        for k, raw_id in enumerate(route):
            task_id = int(raw_id)
            if not 0 <= task_id < len(ga.allTasks):
                errors.append(f"Invalid task id {task_id}")
                continue
            task = ga.allTasks[task_id]
            dt, recorded_energy = float(times[u][k]), float(energies[u][k])
            l1 = float(drone.costMatrix[position, task.startPositionId])
            l2 = float(drone.costMatrix[task.startPositionId, task.endPositionId])
            distance = l1 + l2
            if not math.isfinite(dt) or dt < 0 or not math.isfinite(recorded_energy) or recorded_energy < 0:
                errors.append(f"UAV {u}, step {k}: invalid duration/energy")
                continue
            velocity = distance / dt if dt > 0 else None
            if distance > 0 and (velocity is None or not 1 - 1e-5 <= velocity <= drone.maxVelocity + 1e-5):
                errors.append(f"UAV {u}, step {k}: speed outside bounds")
            if distance > 0 and velocity is not None and velocity > 0:
                recomputed = (
                    drone.cd * drone.rho * drone.Ad * distance * velocity**2
                    + l2 * math.sqrt(((drone.mass + task.packageMass) * drone.g)**3)
                    / (velocity * drone.Fm * math.sqrt(2 * drone.rho * drone.Ar))
                    + l1 * math.sqrt((drone.mass * drone.g)**3)
                    / (velocity * drone.Fm * math.sqrt(2 * drone.rho * drone.Ar))
                ) / drone.eta
            else:
                recomputed = 0.0
            if not math.isclose(recorded_energy, recomputed, rel_tol=1e-6, abs_tol=1e-3):
                errors.append(f"UAV {u}, step {k}: energy formula mismatch")
            battery -= recomputed
            total += recomputed
            elapsed += dt
            if battery < -1e-3:
                errors.append(f"UAV {u}, step {k}: battery exhausted")
            if task.packageMass > drone.maxPayloadMass + 1e-9:
                errors.append(f"UAV {u}, step {k}: payload exceeded")
            if not task.isChargingPoint():
                delivery_ids.append(task_id)
                timely = elapsed <= task.maxDeliveryWindow + 1e-4
                on_time += timely
                if const.MANDATORY_DELIVERY_WINDOW and not timely:
                    errors.append(f"UAV {u}, task {task_id}: deadline exceeded")
            rows.append({"uav": u, "task": task_id, "charging": task.isChargingPoint(),
                         "duration_s": dt, "completion_s": elapsed, "velocity_m_s": velocity,
                         "energy_j": recomputed, "battery_before_swap_j": battery,
                         "deadline_s": None if task.isChargingPoint() else task.maxDeliveryWindow})
            if task.isChargingPoint():
                battery = drone.batteryCapacity
            position = task.endPositionId
        totals.append(total)
    if Counter(delivery_ids) != Counter(range(ga.NT)):
        errors.append("Delivery tasks missing, duplicated, or unexpected")
    percentage = on_time / ga.NT if ga.NT else 1.0
    factor = 1.0 if const.MANDATORY_DELIVERY_WINDOW else (1.0 / percentage if percentage else math.inf)
    expected = factor * (const.ALPHA * max(totals, default=0) + const.BETA * sum(totals))
    actual = float(ga.getSolution().getEvaluation())
    if not math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-3):
        errors.append("Score does not match independently recomputed objective")
    return {"valid": not errors, "errors": errors, "energy_j": sum(totals),
            "score": actual, "recomputed_score": expected, "on_time_fraction": percentage,
            "charging_visits": sum(row["charging"] for row in rows), "steps": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["all", *SCENARIOS], default="all")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="results")
    parser.add_argument("--variant", choices=["V1", "V2", "V3", "V4"], default="V1")
    parser.add_argument("--profile", choices=["repo", "chapter5"], default="repo")
    args = parser.parse_args()
    const.MANDATORY_DELIVERY_WINDOW = args.variant in ("V1", "V3")
    const.RC_ONLY_END = args.variant in ("V3", "V4")
    if args.profile == "chapter5":
        const.BEST_TAKEN = 5
        const.LAST_ITER_CHECKED = 8
        const.DELTA_TOLERANCE = 300
        const.MAX_ITER = 20
        # Match the common drag coefficient explicitly stated in Chapter 5.
        original_init = Uav.__init__
        def chapter5_uav_init(self, *positional, **kwargs):
            kwargs['cd'] = 0.3
            original_init(self, *positional, **kwargs)
        Uav.__init__ = chapter5_uav_init
    for key in ['NP', 'BEST_TAKEN', 'PC', 'PM', 'MAX_ITER', 'GROUP_MUTATION_NUMBER']:
        setattr(GeneticAlgo, key, getattr(const, key))
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    original_run = GeneticAlgo.run
    selected = SCENARIOS if args.scenario == "all" else {args.scenario: SCENARIOS[args.scenario]}
    failed = False
    for name, filename in selected.items():
        random.seed(args.seed)
        np.random.seed(args.seed)
        report = {"scenario": name, "script": filename, "seed": args.seed,
                  "variant": args.variant, "profile": args.profile,
                  "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in Path('.').glob('*.py')},
                  "versions": {"numpy": np.__version__, "scipy": scipy.__version__},
                  "config": {key: getattr(const, key) for key in
                             ["NP", "BEST_TAKEN", "PC", "PM", "MAX_ITER", "LAST_ITER_CHECKED",
                              "DELTA_TOLERANCE", "ALPHA", "BETA",
                              "MANDATORY_DELIVERY_WINDOW", "RC_ONLY_END"]}, "runs": []}
        def recorded_run(ga):
            if name == 'simple' and args.variant == 'V2' and not report['runs']:
                points = Positions()
                fig, ax = plt.subplots(figsize=(8, 6))
                for j, task in enumerate(ga.tasks):
                    start, end = points.getPoint(task.startPositionId), points.getPoint(task.endPositionId)
                    ax.plot([start.getX(), end.getX()], [start.getY(), end.getY()], label=f'Task {j}')
                    ax.scatter(start.getX(), start.getY(), marker='^', color='black')
                    ax.scatter(end.getX(), end.getY(), marker='v', color='black')
                for cp in ga.chargingPoints:
                    point = points.getPoint(cp.startPositionId)
                    ax.scatter(point.getX(), point.getY(), marker='+', s=100, color='gray')
                for u, drone in enumerate(ga.uavs):
                    point = points.getPoint(drone.startPositionId)
                    ax.scatter(point.getX(), point.getY(), marker='s', label=f'UAV {u} start')
                ax.set(xlabel='Longitude', ylabel='Latitude', title='Simple scenario: operating environment')
                ax.legend()
                fig.savefig(output / 'Figure_5_1_environment.png', dpi=150, bbox_inches='tight')
                plt.close(fig)
            started = time.perf_counter()
            original_run(ga)
            result = {"run": len(report["runs"]) + 1, "solution_found": bool(ga.solutionFound),
                      "wall_time_s": time.perf_counter() - started,
                      "iterations": ga.iterationNumber, "uavs": ga.NU, "tasks": ga.NT,
                      "charging_points": ga.NCP, "cpu_time_s": ga.algoTime,
                      "input": {"uav_drag_coefficients": [u.cd for u in ga.uavs],
                                "task_payloads_kg": [t.packageMass for t in ga.tasks],
                                "task_deadlines_s": [t.maxDeliveryWindow for t in ga.tasks]},
                      "best_score_history": [float(v) for v in ga.solutionEvaluations]}
            if ga.solutionFound:
                result["validation"] = check_schedule(ga)
            report["runs"].append(result)
            # Save after each run so lengthy Monte Carlo campaigns retain progress.
            (output / f"{name}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(f"{name}: run {result['run']} finished, solution={result['solution_found']}",
                  file=progress_stream, flush=True)
        GeneticAlgo.run = recorded_run
        def save_figures():
            for number in plt.get_fignums():
                plt.figure(number).savefig(output / f"{name}_figure_{number}.png", dpi=150, bbox_inches="tight")
        plt.show = save_figures
        import sys
        progress_stream = sys.stdout
        started = time.perf_counter()
        with (output / f"{name}.log").open("w", encoding="utf-8", buffering=1) as log:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                try:
                    runpy.run_path(filename, run_name="__main__")
                    invalid = any(not run["validation"]["valid"] for run in report["runs"] if run["solution_found"])
                    report["status"] = "invalid_solution" if invalid else "completed"
                    failed |= invalid
                except Exception:
                    report["status"] = "runtime_error"
                    report["exception"] = traceback.format_exc()
                    print(report["exception"])
                    failed = True
        report["wall_time_s"] = time.perf_counter() - started
        (output / f"{name}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"{name}: {report['status']}, {len(report['runs'])} runs, {report['wall_time_s']:.1f}s", flush=True)
        plt.close("all")
    GeneticAlgo.run = original_run
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
