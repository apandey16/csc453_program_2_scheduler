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
    events = []
    for job_id, arrival_time, run_time in jobs:
        events.append((arrival_time, 'arrival', job_id, run_time))
    
    events.sort()
    
    cur_time = 0
    ready_queue = []
    sim_schedule = []
    job_start_times = {}
    
    event_idx = 0
    
    while event_idx < len(events) or ready_queue:
        while event_idx < len(events) and events[event_idx][0] <= cur_time:
            arrival_time, event_type, job_id, run_time = events[event_idx]
            ready_queue.append((run_time, job_id, arrival_time, run_time))
            ready_queue.sort()
            event_idx += 1
        
        if ready_queue:
            remaining_time, job_id, arrival_time, original_run_time = ready_queue.pop(0)
            
            if job_id not in job_start_times:
                job_start_times[job_id] = cur_time
            
            next_event_time = float('inf')
            if event_idx < len(events):
                next_event_time = events[event_idx][0]
            
            run_time = min(1, remaining_time, next_event_time - cur_time)
            if run_time <= 0:
                run_time = 1
            
            cur_time += run_time
            remaining_time -= run_time
            
            if remaining_time > 0:
                ready_queue.append((remaining_time, job_id, arrival_time, original_run_time))
                ready_queue.sort()
            else:
                turnaround_time = cur_time - arrival_time
                wait_time = turnaround_time - original_run_time
                sim_schedule.append((job_id, wait_time, turnaround_time, arrival_time))
        else:
            if event_idx < len(events):
                cur_time = events[event_idx][0]
            else:
                break
    
    return sorted(sim_schedule, key=lambda x: (x[3], x[0]))

def round_robin_scheduler(jobs, quantum):
    events = []
    for job_id, arrival_time, run_time in jobs:
        events.append((arrival_time, 'arrival', job_id, run_time))
    
    events.sort()
    
    cur_time = 0
    ready_queue = []
    sim_schedule = []
    
    event_idx = 0
    
    while event_idx < len(events) or ready_queue:
        while event_idx < len(events) and events[event_idx][0] <= cur_time:
            arrival_time, event_type, job_id, run_time = events[event_idx]
            ready_queue.append((job_id, arrival_time, run_time, run_time))
            event_idx += 1
        
        if ready_queue:
            job_id, arrival_time, remaining_time, original_run_time = ready_queue.pop(0)
            
            run_time = min(quantum, remaining_time)
            cur_time += run_time
            remaining_time -= run_time
            
            while event_idx < len(events) and events[event_idx][0] <= cur_time:
                arr_time, event_type, arr_job_id, arr_run_time = events[event_idx]
                ready_queue.append((arr_job_id, arr_time, arr_run_time, arr_run_time))
                event_idx += 1
            
            if remaining_time > 0:
                ready_queue.append((job_id, arrival_time, remaining_time, original_run_time))
            else:
                turnaround_time = cur_time - arrival_time
                wait_time = turnaround_time - original_run_time
                sim_schedule.append((job_id, wait_time, turnaround_time, arrival_time))
        else:
            if event_idx < len(events):
                cur_time = events[event_idx][0]
            else:
                break
    
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
