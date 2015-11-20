# launchabel: Launch IPython and Jupyter on Abel

Written as part of the Simula BioComp Hackation 2015, along with [fenicsbot](https://github.com/funsim/fenicsbot) and others.

A script to run and connect to a job on [Abel](http://www.uio.no/english/services/it/research/hpc/abel/).
The script does:

1. forward a local port (default: 9999) to an Abel login node.
2. generate sbatch and srun scripts and send them
3. the sbatch script mostly just calls srun
3. the srun script runs:
   1. node-0: launch notebook server, complete port-forwarding from login node to work node
   2. node 1: start ipcontroller
   3. node 2-n+2 (n nodes): mpirun ipengine

So when you request `-n 2`, you will get 2 engines, but the allocation will request 4 total tasks.

### Examples


    ./launchabel --account=myaccount -n 2
    
    export ABEL_ACCOUNT=myacct
    ./launchabel -n 32 --mem 2G --port 8888
  
  Arguments after `--` are added as SBATCH directives
      ./launchabel -n 1 -- --job-name=test

Or you can reuse more elaborate sbatch config by writing the lines to a file (e.g. `sbatch.sh`):

    #SBATCH --account=myacct
    #SBATCH --mem-per-cpu=8G
    #SBATCH --ntasks=4
    #SBATCH --cpus-per-task=4
  
  and load it with
  
      ./launchabel --sbatch-file=./sbatch.sh
      
in which case the script will not modify *any* SBATCH lines.
