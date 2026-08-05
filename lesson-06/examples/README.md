# Lesson 06 Networking Lab

These notebooks are teaching labs. They simulate firewall behavior so that packet filtering,
stateful rules, default-deny policy, segmentation, and logs can be inspected without configuring a
real production firewall.

The simulator is intentionally small. Real hospitals normally use operating-system firewalls,
network appliances, cloud security groups, or managed firewall platforms. Administrators define and
maintain the policy; the enforcement engine is provided by the chosen system.

## Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r lesson-06/examples/requirements.txt
jupyter notebook lesson-06/examples
```

The lab logic itself uses only the Python standard library. If Jupyter is not available, run the
script version directly:

```bash
python3 lesson-06/examples/firewall_policy_simulator.py
```

## Notebooks

- `01_firewall_policy_simulator.ipynb`: ordered packet filtering, default deny, stateful replies, DMZ policy, VPN access, and log analysis.
- `firewall_policy_simulator.py`: the same core lab as a plain Python script.

## Optional Real-System Extensions

- **Mininet** can emulate a small network with Linux hosts, switches, and links. It is realistic, but usually needs Linux, root privileges, and sometimes a VM.
- **Scapy** can craft and inspect packets. It is excellent for seeing packet fields, but sending packets commonly requires administrator privileges.
- **iptables/nftables** are real Linux firewall tools. They are powerful, but should be practiced in a VM or disposable lab environment.
