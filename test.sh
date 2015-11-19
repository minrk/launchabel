#SBATCH

env
if [[ "$SLURM_PROCID" = "0" ]]; then
  echo "hi"
else
  mpirun python -c "import os; print(os.getpid())"
fi
