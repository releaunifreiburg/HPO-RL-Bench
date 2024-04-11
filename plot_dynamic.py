import json
import os
import numpy as np
from scipy.stats import rankdata
import matplotlib.pyplot as plt
from matplotlib import rcParams
# Setting global plot parameters
rcParams["font.size"] = "22"
plt.rcParams["figure.figsize"] = (8,7)
# Define constants for environments, algorithms, methods, and method colors
ENVIRONMENTS_DYNAMIC = ['CartPole-v1', 'MountainCar-v0', 'Acrobot-v1', 'Pendulum-v0', 'Enduro-v0']
ALGORITHMS = ["PPO"]
ENVIRONMENTS = {"DYNAMIC": ENVIRONMENTS_DYNAMIC}
METHODS = ["RS", "GP", "Optuna", "SMAC", "DyHPO", "PBT", "PB2", "D-PBT", "D-PB2"]
COLORS = {"RS": "slategrey", "GP": "orange", "Optuna": "darkgoldenrod", "SMAC": "red", "DyHPO": "purple", "PB2": "blue",
          "PBT": "limegreen", "D-PBT": "darkgreen", "D-PB2": "navy"}


fig = plt.figure()
SEEDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def get_return_at_budget(budget, budgets_method, returns_method):
    """
    Fetches the return for a method given a specific budget. Handles cases outside the budget range.

    Parameters:
    - budget: The specified budget.
    - budgets_method: List of budgets for the method.
    - returns_method: Corresponding returns for the budgets.

    Returns:
    - Return value at the given budget or extrapolation if out of range.
    """
    # Handle case where budget is below the method minimum
    if budget < budgets_method[0]:
        return -np.inf
    # Handle case where budget is above the method maximum
    elif budget > budgets_method[-1]:
        return returns_method[-1]
    else:
        # Find closest budget not exceeding the specified budget
        min_dist = np.inf
        k_min = 0
        for k, bud in enumerate(budgets_method):
            if bud <= budget:
                if budget - bud < min_dist:
                    min_dist = budget - bud
                    k_min = k
        return returns_method[k_min]


# Loop through each environment type and its environments
for ENV_TYPE, ENVIRONMENT_LIST in ENVIRONMENTS.items():
    # Initialize storage for data and budgets
    data_all = {method: [] for method in METHODS}
    budgets_all = {method: [] for method in METHODS}
    # Iterate through seeds and environments
    for seed in SEEDS:
        for environment in ENVIRONMENT_LIST:
            # Iterate through algorithms and methods
            for algorithm in ALGORITHMS:
                for method in METHODS:
                    method_file_name = method.replace('-', '_')
                    with open(os.path.join('plot_data', f'{method_file_name}_seed{seed}_{environment}_{algorithm}_dyn.json')) as f:
                        data = json.load(f)
                        budgets_all[method].append(data["wallclock_time_eval"])
                        data_all[method].append(data["incumbents"])
    # Rank aggregation over seeds and environments
    all_ranks = {method: [] for method in METHODS}
    all_data_timesteps = []
    for data in range(len(data_all["PBT"])):
        # Combine and sort unique budgets from PBT and PB2 for comparison of methods across these budgets
        budgets = budgets_all["PBT"][data] + budgets_all["PB2"][data]
        budgets_sorted = np.unique(sorted(budgets))
        all_data_timesteps.append(budgets_sorted)
    # Find the run with the longest budget sequence for reference
    longest_run = np.argmax([timestep[-1] for timestep in all_data_timesteps])
    budgets_sorted = all_data_timesteps[longest_run]

    for data in range(len(data_all["PBT"])):
        ranks_method = {method: [] for method in METHODS}
        timesteps = budgets_sorted.tolist()
        # Calculate returns at each budget for all methods
        for i in range(len(budgets_sorted)):
            returns = {method: -np.inf for method in METHODS}
            for method in METHODS:
                return_ = get_return_at_budget(budgets_sorted[i], budgets_all[method][data], data_all[method][data])
                returns[method] = return_

            perf = []
            indexes = {method: -1 for method in METHODS}
            for method in METHODS:
                if returns[method] != -np.inf:
                    perf.append(-1 * returns[method])
                    indexes[method] = len(perf) - 1

            ranks = rankdata(perf, method='min')
            # Assign ranks or infinity for methods not evaluated at this budget
            for method in METHODS:
                if indexes[method] != -1:
                    ranks_method[method].append(ranks[indexes[method]])
                else:
                    ranks_method[method].append(np.inf)
        for method in METHODS:
            all_ranks[method].append(ranks_method[method])
        all_data_timesteps.append(timesteps)

    # Calculate average and standard error of ranks across all seeds and environments
    avg_ranks = {method: [] for method in METHODS}
    std_ranks = {method: [] for method in METHODS}
    for method in METHODS:
        min_len = np.amin([len(ranks) for ranks in all_ranks[method]])
        avg_ranks[method] = np.mean([ranks[:min_len] for ranks in all_ranks[method]], axis=0)
        std_ranks[method] = np.std([ranks[:min_len] for ranks in all_ranks[method]], axis=0) / np.sqrt(
            len(ENVIRONMENT_LIST)
            * len(SEEDS))

    timesteps_plot = budgets_sorted
    plt.ylabel("Average Rank")
    plt.xlabel("Wallclock Time (s)")

    plt.xlim((timesteps_plot[0], timesteps_plot[-1]))

    for method in METHODS:
        plt.plot(timesteps_plot, avg_ranks[method], label=method, color=COLORS[method], lw=3)
        plt.fill_between(timesteps_plot, avg_ranks[method] + std_ranks[method], avg_ranks[method] - std_ranks[method],
                        color=COLORS[method], alpha=0.1)

    plt.ticklabel_format(style='sci', axis='x', scilimits=(1, 4))
plt.tight_layout()
plt.subplots_adjust(left=0.15, bottom=0.38, right=0.85, top=None, wspace=0.15, hspace=0.35)
plt.legend(bbox_to_anchor=(0.5, 0.02), loc="lower center",
                bbox_transform=fig.transFigure, ncol=3)
plt.savefig(f"Dynamic_{ALGORITHMS[0]}_std_err_wallclock.pdf")
plt.show()
plt.clf()
