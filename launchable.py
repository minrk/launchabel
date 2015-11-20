#!/usr/bin/env python
"""
Usage: python launchable.py
"""
from __future__ import print_function

tpls = {'setup': '''
mkdir -p $HOME/launchable
tempdir=$(mktemp -d --tmpdir="$HOME/launchable")
TUNNEL_PORT={tunnel_port}
NB_PORT={nb_port}
LOGIN_NODE=$(hostname)
''',

'scripts': '''
batch="$tempdir/batch.sh"
run="$tempdir/run.sh"

cat >"$batch" <<EOL
#!/bin/bash
#SBATCH --account=nn9279k
#SBATCH --time=00:15:00
#SBATCH --mem-per-cpu=100M
#SBATCH --ntasks={n}
srun "$run"
EOL

cat >"$run" <<EOL
#!/bin/bash
source /etc/profile
source /cluster/bin/jobsetup
source /usit/abel/u1/oyvinev/fenics1.6_jupyter

if [[ "\$SLURM_PROCID" = "0" ]]; then
  ssh -R $TUNNEL_PORT:localhost:$NB_PORT $LOGIN_NODE -f -N
  jupyter notebook --port $NB_PORT
elif [[ "\$SLURM_PROCID" = "1" ]]; then
  ipcontroller --ip='*'
elif [[ "\$SLURM_PROCID" = "2" ]]; then
  mpirun --bind-to none -n "\$((SLURM_NTASKS-2))" ipengine
fi

EOL

chmod +x $run $batch
echo BATCH:$batch
echo RUN:$run
''',

'run': '''
jobid=$(/cluster/bin/sbatch $batch | awk '{{print $4}}')
echo "job id: $jobid"
test -z "$jobid" && exit 1

state="wait"
while [[ "$state" = "wait" ]]; do
  echo .
  # check squeue
  test -z "$(squeue -u `whoami` | grep $jobid)" && state='FAILED'
  curl -s http://localhost:$TUNNEL_PORT 2>&1 >/dev/null && state=AOK || sleep 1
done

echo "$state"

if [[ "$state" = "FAILED" ]]; then
  while [[ ! -f "$HOME/slurm-$jobid.out ]]; do
    sleep 1
  end
  cat ~/slurm-$jobid.out
  exit 1
fi

while true; do
  sleep 30
done
'''}

import argparse
from random import randint
import sys
import webbrowser

import pexpect


def expect_echo(p):
    p.sendline('###END###')
    p.expect('###END###')


def run_job(options):
    ns = options.__dict__
    print("Tunneling {local_port} to {host}:{tunnel_port}".format(**ns))
    p = pexpect.spawn('ssh', [
            '-L',
            '%i:localhost:%i' % (options.local_port, options.tunnel_port),
            options.host,
            'bash',
    ])
    p.logfile = sys.stderr
    print('setup')
    p.send(tpls['setup'].format(**ns))
    expect_echo(p)
    print('scripts')
    p.send(tpls['scripts'].format(**ns))
    expect_echo(p)
    print('run')
    p.send(tpls['run'].format(**ns))
    expect_echo(p)
    p.expect('job id:')
    p.expect('\r\n')
    jobid = int(p.before)
    try:
        p.expect(['AOK', 'FAILED'], timeout=60)
    except pexpect.EOF:
        print("Failed")
        print(p.before, file=sys.stderr)
        sys.exit(1)
    if p.after == 'FAILED':
        print("Failed")
        # got failed message, wait for EOF and show output
        p.expect(pexpect.EOF)
        print(p.before, file=sys.stderr)
        sys.exit(1)
    return p

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=4)
    parser.add_argument('--port', dest='local_port', type=int, default=9999)
    parser.add_argument('--tunnel-port', type=int, default=randint(49152, 65535))
    parser.add_argument('--nb-port', type=int, default=randint(49152, 65535))
    parser.add_argument('--host', type=str, default='kerbin')
    options = parser.parse_args()
    p = run_job(options)
    print("done")
    webbrowser.open('http://localhost:9999')
    # wait for exit
    p.expect(pexpect.EOF, timeout=None)

if __name__ == '__main__':
    main()
