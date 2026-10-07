from GeneticAlgo import GeneticAlgo
from AlgoConstants import AlgoConstants as cst
import statistics
from typing import List

def monteCarloRun(envComplexA, printGraph):
    energies = []
    tasksExecuted = []
    chargeExecuted = []
    iterations = []
    runTime = []

    for i in range(20):
        print("RUN " + str(i))
        ga = GeneticAlgo(envComplexA, printGraph=printGraph)
        ga.run()
        if ga.solutionFound:
            energies.append(totalEnergy(ga.getSolution().getChromosome().getEnergyPerTaskPerUav())/10**6)
            if not cst.MANDATORY_DELIVERY_WINDOW:
                tasksExecuted.append(ga.getSolution().getChromosome().getRespectDeliveryPercentage())
            chargeExecuted.append(numberOfChargingTask(ga.getSolution().getChromosome().getTasksOrder()))
            iterations.append(ga.iterationNumber)
            runTime.append(ga.algoTime)

    print("Number of solutions: " + str(len(energies)))
    if not energies:
        print("No feasible solution found in 20 runs; no statistics available.")
        return
    print("TOTAL ENERGY [MJ]")
    print("mean: " + str(statistics.mean(energies)))
    print("stdev: " + str(statistics.stdev(energies) if len(energies) > 1 else 0.0))
    if not cst.MANDATORY_DELIVERY_WINDOW:
        print("TASKS EXECUTED")
        print("mean: " + str(statistics.mean(tasksExecuted)))
        print("stdev: " + str(statistics.stdev(tasksExecuted) if len(tasksExecuted) > 1 else 0.0))
    print("CHARGE EXECUTED")
    print("mean: " + str(statistics.mean(chargeExecuted)))
    print("stdev: " + str(statistics.stdev(chargeExecuted) if len(chargeExecuted) > 1 else 0.0))
    print("ITERATIONS")
    print("mean: " + str(statistics.mean(iterations)))
    print("stdev: " + str(statistics.stdev(iterations) if len(iterations) > 1 else 0.0))
    print("ALGO TIME")
    print("mean: " + str(statistics.mean(runTime)))
    print("stdev: " + str(statistics.stdev(runTime) if len(runTime) > 1 else 0.0))

def numberOfChargingTask(taskOrder: List[int]) -> int:
    output = 0
    for t in taskOrder:
        if cst.NT <= t < cst.NT + cst.NCP:
            output += 1
    
    return output

def totalEnergy(energyPerUav):
    totalEnergy = 0
    for u in energyPerUav:
        for e in u:
            totalEnergy += e
    
    return totalEnergy
