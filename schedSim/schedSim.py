#!/usr/bin/env python3

import argparse
import sys

def validate_algorithm(algorithm):
    if algorithm.upper() not in ['SRTN', 'FIFO', 'RR']:
        return False
    return True

def validate_quantum(quantum):
    if quantum < 1:
        return False
    return True

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('job_file', type=str)
    parser.add_argument('-p', '--algorithm', type=str, default='FIFO')
    parser.add_argument('-q', '--quantum', type=int, default=1)
    
    args = parser.parse_args()
    
    if not validate_algorithm(args.algorithm):
        args.algorithm = 'FIFO'
    else:
        args.algorithm = args.algorithm.upper()
    
    if args.algorithm == 'RR':
        if not validate_quantum(args.quantum):
            print("Error: Quantum must be a positive", file=sys.stderr)
            sys.exit(1)
    
    return args.job_file, args.algorithm, args.quantum

def read_job_file(filename):
    jobs = []
    try:
        with open(filename, 'r') as f:
            for job_id, line in enumerate(f):
                arrival_time, run_time = map(int, line.strip().split())
                jobs.append((job_id, arrival_time, run_time))
    except Exception as e:
        print("Error parsing job file: ", e)
        sys.exit(1)
    return jobs

def fifo(jobs):
    sorted_jobs = sorted(jobs, key=lambda x: (x[1], x[0]))
    cur_time = 0
    sim_schedule = []
    
    for job_id, arrival_time, run_time in sorted_jobs:
        if arrival_time > cur_time:
            cur_time = arrival_time
        wait_time = cur_time - arrival_time
        turnaround_time = wait_time + run_time
        sim_schedule.append((job_id, wait_time, turnaround_time, arrival_time))
        
        cur_time += run_time
    
    return sorted(sim_schedule, key=lambda x: (x[3], x[0]))

def srtn_scheduler(jobs):
    sorted_jobs = sorted(jobs, key=lambda x: (x[1], x[0]))
    cur_time = 0
    sim_schedule = []
    
    job_metadata = {}
    for job_id, arrival_time, run_time in sorted_jobs:
        job_metadata[job_id] = {"remaining": run_time, "arrival": arrival_time, "wait": 0, "turnaround": 0}

    while job_metadata:
        possible_jobs = []
        for job_id in job_metadata:
            if job_metadata[job_id]["arrival"] <= cur_time:
                possible_jobs.append((job_id, job_metadata[job_id]["remaining"]))
        
        if possible_jobs:
            running_job, execution_time = min(possible_jobs, key=lambda x: (x[1], x[0]))

            job_metadata[running_job]["remaining"] -= 1
            job_metadata[running_job]["turnaround"] += 1
            
            for job_id, execution_time in possible_jobs:
                if job_id != running_job:  
                    job_metadata[job_id]["wait"] += 1
                    job_metadata[job_id]["turnaround"] += 1
            
            if job_metadata[running_job]["remaining"] == 0:
                sim_schedule.append((running_job, job_metadata[running_job]["wait"], job_metadata[running_job]["turnaround"], job_metadata[running_job]["arrival"]))
                del job_metadata[running_job]
        
        cur_time += 1
    
    return sorted(sim_schedule, key=lambda x: (x[3], x[0]))

def round_robin_scheduler(jobs, quantum):
    sorted_jobs = sorted(jobs, key=lambda x: (x[1], x[0]))
    cur_time = 0
    sim_schedule = []
    
    job_metadata = {}
    for job_id, arrival_time, run_time in sorted_jobs:
        job_metadata[job_id] = { "remaining": run_time, "arrival": arrival_time, "wait": 0, "last_run": arrival_time }
    
    ready_queue = []
    
    while job_metadata:
        for job_id, arrival_time, execution_time in sorted_jobs:
            if job_id in job_metadata and job_metadata[job_id]["arrival"] <= cur_time and job_id not in ready_queue:
                ready_queue.append(job_id)
        
        if ready_queue:
            running_job = ready_queue.pop(0)

            job_metadata[running_job]["wait"] += cur_time - job_metadata[running_job]["last_run"]
            
            if job_metadata[running_job]["remaining"] >= quantum:
                time_slice = quantum
            else:
                time_slice = job_metadata[running_job]["remaining"]
            
            job_metadata[running_job]["remaining"] -= time_slice
            job_metadata[running_job]["last_run"] = cur_time + time_slice
            cur_time += time_slice
            
            for job_id, arrival_time, execution_time in sorted_jobs:
                if job_id in job_metadata and job_metadata[job_id]["arrival"] <= cur_time and job_id not in ready_queue and job_id != running_job:
                    ready_queue.append(job_id)
            
            if job_metadata[running_job]["remaining"] == 0:
                turnaround_time = cur_time - job_metadata[running_job]["arrival"]
                sim_schedule.append((running_job, job_metadata[running_job]["wait"], turnaround_time, job_metadata[running_job]["arrival"]))
                del job_metadata[running_job]
            else:
                ready_queue.append(running_job)
        else:
            cur_time += 1
    
    return sorted(sim_schedule, key=lambda x: (x[3], x[0]))

def display_simulated_schedule(sim_schedule):
    total_turnaround = 0
    total_wait = 0
    job_ctr = 0
    
    for job_id, wait_time, turnaround_time, arrival_time in sim_schedule:
        print(f"Job {job_id:3d} -- Turnaround {turnaround_time:3.2f}  Wait {wait_time:3.2f}")
        total_turnaround += turnaround_time
        total_wait += wait_time
        job_ctr += 1
    
    avg_turnaround = total_turnaround / job_ctr
    avg_wait = total_wait / job_ctr
    print(f"Average -- Turnaround {avg_turnaround:3.2f}  Wait {avg_wait:3.2f}")

def main():
    job_file, algorithm, quantum = parse_arguments()
    jobs = read_job_file(job_file)
    
    if algorithm == "SRTN":
        sim_schedule = srtn_scheduler(jobs)
    elif algorithm == "RR":
        sim_schedule = round_robin_scheduler(jobs, quantum)
    else:
        sim_schedule = fifo(jobs)
    
    display_simulated_schedule(sim_schedule)

if __name__ == "__main__":
    main()
