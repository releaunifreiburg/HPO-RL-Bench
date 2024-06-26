from benchmark_handler import BenchmarkHandler
from optimizers.optuna import Optuna


search_space = "PPO"

benchmark = BenchmarkHandler(environment="Pong-v0",
                             search_space=search_space,
                             seed=0)

optuna_ = Optuna(search_space_name=search_space, search_space=benchmark.get_search_space(search_space),
                 obj_function=benchmark.get_metrics,
                 max_budget=99, seed=0)

n_iters = 10
best_conf, best_score = optuna_.suggest(n_iterations=n_iters)
print(f"Best configuration found is {best_conf}")
print(f"Best final evaluation return is {best_score}")



