from benchmark_handler import BenchmarkHandler
from optimizers.dyhpo import DyHPO
from optimizers.dyhpo_utils import AutoRLBench


search_space = "PPO"

benchmark = BenchmarkHandler(environment="Pong-v0",
                             search_space=search_space,
                             return_metrics=["eval_avg_returns"],
                             seed=0)
hporrlbench_data = AutoRLBench(path_to_json_files='',
                               ss_name=search_space,
                               env_name='Pong-v0',
                               seed=0)
dyhpo = DyHPO(search_space_name=search_space, search_space=benchmark.get_search_space(search_space),
              obj_function=benchmark.get_metrics, max_budget=99, seed=0,
              min_value=hporrlbench_data.min_value, max_value=hporrlbench_data.max_value)
n_iters = 20
print("Running DyHPO")
best_conf, best_score = dyhpo.suggest(n_iterations=n_iters)
print(f"Best configuration found is {best_conf}")
print(f"Best final evaluation return is {best_score}")



