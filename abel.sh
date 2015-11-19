#!/bin/bash
#SBATCH

if [[ "$SLURM_PROCID" = "0" ]]; then
  ssh -R 0.0.0.0:9999:localhost:8888  -f -N login-0-1
  jupyter notebook
elif [[ "$SLURM_PROCID" = "1" ]]; then
  ipcontroller --ip='*'
elif [[ "$SLURM_PROCID" = "2" ]]; then
  mpirun --bind-to=none -n "$((SLURM_NTASKS))" ipengine
fi
