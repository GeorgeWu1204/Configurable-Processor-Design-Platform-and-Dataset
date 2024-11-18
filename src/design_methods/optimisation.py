import torch
import time
import definitions
import design_methods.utils as utils
import warnings
from colorama import Fore, Style

from design_methods.sampler import initial_sampler
from design_methods.BO.optimisation_models import select_model
from design_methods.train_set import train_set_records
from botorch.sampling.normal import SobolQMCNormalSampler
from botorch.fit import fit_gpytorch_model

# Warning Suppression
from botorch.exceptions import BadInitialCandidatesWarning
from linear_operator.utils.cholesky import NumericalWarning
from botorch.exceptions.warnings import InputDataWarning

from design_methods.processor_analyser import build_processor_analyser
from design_methods.train_set import train_set_records

# Train Set Settings
TRAIN_SET_DISTURBANCE_RANGE = 0.01                  # noise standard deviation for objective
TRAIN_SET_ACCEPTABLE_THRESHOLD = 0.2                # acceptable distance between the rounded vertex and the real vertex

# optimisation_model Settings
NUM_RESTARTS = 4                # number of starting points for BO for optimize_acqf
NUM_OF_INITIAL_POINT = 2        # number of initial points for BO  Note: has to be power of 2 for sobol sampler
N_TRIALS = 1                    # number of trials of BO (outer loop)
N_BATCH = 15                    # number of BO batches (inner loop)
BATCH_SIZE = 1                  # batch size of BO (restricted to be 1 in this case)
MC_SAMPLES = 128                # number of MC samples for qNEI
RAW_SAMPLES = 8                 # number of raw samples for qNEI

class Design_Framework:
    def __init__(self, param_space_info, objective_space_info, processor_dataset, device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu"), t_type = torch.float64, model_type = 'single_objective_BO'):
        # TODO: Add automatic device detection
        self.device = device
        self.t_type = t_type
        self.param_space_info = param_space_info
        self.objective_space_info = objective_space_info
        self.processor_analyser = build_processor_analyser(param_space_info, objective_space_info, processor_dataset, t_type, device)

        print("<-------------- Optimisation Settings -------------->")
        print(f"Input Names: {self.param_space_info.input_names}")
        print(f"Input Self Constraints: {self.param_space_info.self_constraints}")
        print(f"Input Offset: {self.param_space_info.input_offsets}")
        print(f"Input Scales: {self.param_space_info.input_scales}")
        print(f"Input Normalised Factor: {self.param_space_info.input_normalized_factor}")
        print(f"Input Exponential: {self.param_space_info.input_exp}")
        print(f"Input Categories: {self.param_space_info.input_categorical}")
        print(f"Optimisation Target : {self.objective_space_info.optimisation_target}")
        print(f"Objectives to Optimise: {self.objective_space_info.obj_to_optimise}")
        print(f"Output Objective Constraint: {self.objective_space_info.output_constraints}")
        print("<--------------------------------------------------->")

        # Runtime Settings
        self.verbose = True
        self.record = False
        self.plot_posterior = False
        self.enable_train_set_modification = False

        self.debug = True
        if not self.debug:
            warnings.filterwarnings("ignore", category=BadInitialCandidatesWarning)
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            warnings.filterwarnings("ignore", category=NumericalWarning)
            warnings.filterwarnings("ignore", category=InputDataWarning)
            torch.set_printoptions(sci_mode=False)

        # #objective index for hypervolume calculation
        # obj_index = 0

        #reference point for optimisation used for hypervolume calculation
        self.ref_points = utils.find_ref_points(self.objective_space_info.obj_to_optimise_dim, self.processor_analyser.objs_direct, t_type, device)

        #normalise objective to ensure the same scale
        sampler_generator = initial_sampler(param_space_info.input_dim, objective_space_info.obj_to_evaluate_dim, param_space_info.constraints, self.processor_analyser, t_type, device)
        self.train_set_storage = train_set_records(param_space_info.input_normalized_factor, list(param_space_info.self_constraints.values()), param_space_info.conditional_constraints, param_space_info.input_categorical, self.ref_points, objective_space_info.obj_to_optimise_dim, self.enable_train_set_modification, TRAIN_SET_ACCEPTABLE_THRESHOLD, TRAIN_SET_DISTURBANCE_RANGE, t_type, device)

        if self.plot_posterior:
            self.posterior_examiner = utils.test_posterior_result(param_space_info.input_names, t_type, device)
            self.posterior_objective_index = 0
        if self.record:
            record_file_name = '../test/test_results/'
            for obj_name in objective_space_info.obj_to_optimise.keys():
                record_file_name = record_file_name + obj_name + '_'
            self.results_record = utils.recorded_training_result(param_space_info.input_names, objective_space_info.obj_to_optimise, record_file_name, N_TRIALS, N_BATCH)
        
        self.optimisation_model = select_model(model_type, NUM_RESTARTS, RAW_SAMPLES, BATCH_SIZE, self.param_space_info, self.objective_space_info, self.ref_points, sampler_generator, device, t_type)

#TODO: Temporarily modified for paper, change from multi-objective to single-objective while keep using the same dataset.
# objective_space_info.obj_to_optimise = {list(objective_space_info.obj_to_optimise.keys())[obj_index] : list(objective_space_info.obj_to_optimise.values())[obj_index]}

    def run_optimisation(self):
        # Global Best Values
        best_obj_scores_per_trial = []
        best_sample_points_per_trial = {trial : {input : 0.0 for input in self.param_space_info.input_names} for trial in range(1, N_TRIALS + 1)}
        quit()
        #Optimisation Loop
        for trial in range (1, N_TRIALS + 1):

            print(f"\nTrial {trial:>2} of {N_TRIALS} ")
            
            (   train_x_ei,
                exact_obj_ei,
                train_obj_ei,
                obj_score_ei,
            ) = self.optimisation_model.generate_initial_data(NUM_OF_INITIAL_POINT, self.processor_analyser)
        

            print("<----------------Initial Data--------------->")
            print("train_x_ei: ", train_x_ei)                   #shape = (num_samples, input_dim)
            print("train_obj_ei: ", train_obj_ei)               #shape = (num_samples, objs_to_evaluate_dim)
            print("exact_obj_ei: ", exact_obj_ei)               #shape = (num_samples, objs_to_evaluate_dim)
            print("obj_score_ei: ", obj_score_ei)               #shape = (num_samples, 1)
            print("<------------------------------------------->")
            self.train_set_storage.store_initial_data(train_x_ei)
            mll_ei, model_ei = self.optimisation_model.initialize_model(train_x_ei, train_obj_ei)
            #reset the best observation
            best_sample_point_per_interation, best_observation_per_interation, best_constraint_per_interation, best_obj_score_per_interation = \
                definitions.extract_best_from_initialisation_results(train_x_ei, exact_obj_ei, obj_score_ei, self.objective_space_info.obj_to_optimise, self.objective_space_info.output_constraints)
            print("best_sample_point_per_interation: ", best_sample_point_per_interation)
            print("best_obj_score_per_interation: ", best_obj_score_per_interation)

            for iteration in range(1, N_BATCH + 1):
                t0 = time.monotonic()
                # fit the models
                fit_gpytorch_model(mll_ei)
                #QMC sampler
                qmc_sampler = SobolQMCNormalSampler(sample_shape=torch.Size([MC_SAMPLES]))
                #TODO: single acqf -> uses train_obj while multiple acqf uses train_x
                acqf = self.optimisation_model.build_acqf(model_ei, train_obj_ei, qmc_sampler)
                # optimize and get new observation
                valid_generated_sample, new_x_ei, new_exact_obj_ei, new_train_obj_ei, obj_score = self.optimisation_model.optimize_acqf_and_get_observation(acqf, self.processor_analyser)

                # examine the posterior
                if self.plot_posterior and iteration == 10:
                    self.posterior_examiner.examine_posterior(model_ei.subset_output([self.posterior_objective_index]), iteration)
                    # posterior_examiner.examine_acq_function(acqf, iteration)
                    
                # update training points
                valid_point_for_storage, modified_new_train_x, modified_new_train_obj_ei, modified_obj_score  = self.train_set_storage.store_new_data(valid_generated_sample, new_x_ei, new_train_obj_ei, obj_score, self.processor_analyser)
                
                #--------------for self.debug------------------
                if self.debug:
                    print("modified_new_train_x: ", modified_new_train_x)
                    print("modified_new_train_obj_ei: ", modified_new_train_obj_ei)
                    print("modified_obj_score: ", modified_obj_score)

                if valid_point_for_storage:
                    train_x_ei   = torch.cat([train_x_ei, modified_new_train_x])
                    train_obj_ei = torch.cat([train_obj_ei, modified_new_train_obj_ei])
                    obj_score_ei = torch.cat([obj_score_ei, modified_obj_score])
                    if obj_score > best_obj_score_per_interation:
                        best_obj_score_per_interation = obj_score
                        best_observation_per_interation = definitions.encapsulate_obj_tensor_into_dict(self.objective_space_info.obj_to_optimise, new_exact_obj_ei)
                        best_constraint_per_interation = definitions.encapsulate_obj_tensor_into_dict(self.objective_space_info.output_constraints, new_exact_obj_ei[... , 1:])
                        best_sample_point_per_interation = new_x_ei
                
                # reinitialize the models so they are ready for fitting on next iteration
                mll_ei, model_ei = self.optimisation_model.initialize_model(train_x_ei, train_obj_ei)
                t1 = time.monotonic()

                if self.verbose:
                    print(f"{Fore.YELLOW}Iteration: {iteration}{Style.RESET_ALL}")
                    
                    for obj in self.objective_space_info.obj_to_optimise.keys():
                        if best_observation_per_interation[obj] is None:
                            print(f"{Fore.RED}best_value_{obj}: None{Style.RESET_ALL}")
                            continue
                        if(self.objective_space_info.obj_to_optimise[obj] == 'minimise'):
                            print(f"{Fore.RED}best_value_{obj}: {-1 * best_observation_per_interation[obj]}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}best_value_{obj}: {best_observation_per_interation[obj]}{Style.RESET_ALL}")
                    for obj in self.objective_space_info.output_constraints:
                        print(f"{Fore.GREEN}check constraint_{obj}: {best_constraint_per_interation[obj]}{Style.RESET_ALL}")
                else:
                    print(".", end="")
                
                if self.record:
                    tmp_new_obj_ei = {}
                    for obj in self.objective_space_info.obj_to_optimise.keys():
                        if best_observation_per_interation[obj] is None:
                            continue
                        if(self.objective_space_info.obj_to_optimise[obj] == 'minimise'):
                            tmp_new_obj_ei[obj] = -1 * best_observation_per_interation[obj]
                        else:
                            tmp_new_obj_ei[obj] = best_observation_per_interation[obj]
                    self.results_record.self.record(iteration, trial, tmp_new_obj_ei, best_obj_score_per_interation.item(), t1-t0)
            
            print("best_sample_point_per_interation: ", best_sample_point_per_interation)
            best_obj_scores_per_trial.append(best_obj_score_per_interation)
            best_sample_points_per_trial[trial] = best_sample_point_per_interation

            # if self.record:
            #     unnormalized_train_x = utils.recover_single_input_data(train_x_ei, param_space_info.input_normalized_factor, param_space_info.input_scales, param_space_info.input_offsets, param_space_info.input_exp)
            #     results_record.record_input(trial, unnormalized_train_x, obj_score_ei)

        if self.record:
            self.results_record.store()
        # Final stage, find the best sample point and the corresponding best observation
        print("<------------------Final Result------------------>")
        best_trial = definitions.find_max_index_in_list(best_obj_scores_per_trial)
        _, best_objective = self.processor_analyser.find_evaluation_results(best_sample_points_per_trial[best_trial + 1])
        print("best_sample_points_per_trial: ", best_sample_points_per_trial[best_trial + 1])
        real_sample_point = definitions.recover_single_input_data(best_sample_points_per_trial[best_trial + 1].squeeze(0), self.param_space_info.input_normalized_factor, self.param_space_info.input_scales, self.param_space_info.input_offsets, self.param_space_info.input_categorical, self.param_space_info.input_exp)
        print(f"{Fore.BLUE}Best sample point: {real_sample_point}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}Best objective: {best_objective}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}Best hyper volume: {best_obj_scores_per_trial[best_trial]}{Style.RESET_ALL}")