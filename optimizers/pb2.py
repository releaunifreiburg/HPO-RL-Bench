import logging
from ray import tune
from ray.tune.schedulers.pb2 import PB2
logging.basicConfig(level=logging.INFO)
import itertools
from optimizers.optimizer import Optimizer


class CustomStopper(tune.Stopper):
    def __init__(self, max_iter: int = 100):
        self.should_stop = False
        self.max_iter = max_iter

    def __call__(self, trial_id, result):
        return result["training_iteration"] >= self.max_iter

    def stop_all(self):
        return self.should_stop

class PB2Optimizer(Optimizer):

    def __init__(self, search_space_name: str = None, search_space: dict = None, obj_function = None,
                 max_budget: int = 100, seed: int = 0):
        super().__init__(search_space, obj_function)
        self.cartesian_prod_of_configurations = list(itertools.product(*tuple(search_space.values())))
        self.constant_budget = max_budget
        self.search_space_name = search_space_name
        self.seed = seed
        bounds = {}
        for key, value in self.search_space.items():
            bounds[key] = list([min(value), max(value)])
        self.scheduler = PB2(
            hyperparam_bounds=bounds,
            time_attr="training_iteration",
            metric="mean_accuracy",
            mode="max",
            perturbation_interval=33,
            quantile_fraction=0.25,  # copy bottom % with top %
            )
        self.stopper = CustomStopper(max_iter=max_budget)

    def suggest(self, n_iterations: int = 1):
        config_space = {}
        for key, value in self.search_space.items():
            config_space[key] = tune.choice(value)
        analysis = tune.run(
            self.obj_function,
            name="%s_seed%s" % (self.search_space_name, self.seed),
            scheduler=self.scheduler,
            verbose=1,
            stop=self.stopper,
            checkpoint_score_attr="mean_accuracy",
            keep_checkpoints_num=4,
            num_samples=8,
            config=config_space)
        best_conf = analysis.best_config
        best_return = analysis.best_result




        return best_conf, best_return
