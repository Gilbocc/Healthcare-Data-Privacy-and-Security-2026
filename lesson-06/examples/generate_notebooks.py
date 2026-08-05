import json
from pathlib import Path


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip().splitlines(True)}


def code(text):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.strip().splitlines(True),
    }

common_code = r'''
from dataclasses import dataclass
from ipaddress import ip_address, ip_network


def show_table(rows):
    # Print dictionaries as a small fixed-width table without external dependencies.
    if not rows:
        print("(no rows)")
        return
    headers = list(rows[0].keys())
    widths = {
        header: max(len(str(header)), *(len(str(row.get(header, ""))) for row in rows))
        for header in headers
    }
    print(" | ".join(header.ljust(widths[header]) for header in headers))
    print("-+-".join("-" * widths[header] for header in headers))
    for row in rows:
        print(" | ".join(str(row.get(header, "")).ljust(widths[header]) for header in headers))


@dataclass(frozen=True)
class Packet:
    # Human-readable label used in the lab output.
    name: str
    # Source IP address of the packet.
    src_ip: str
    # Destination IP address of the packet.
    dst_ip: str
    # Transport protocol: TCP, UDP, or ICMP in this toy model.
    protocol: str
    # Destination port. ICMP does not use ports, so None is allowed.
    dst_port: int | None
    # Direction of the packet: new request or reply to an existing flow.
    direction: str = "new"


packets = [
    Packet("Doctor opens EHR", "10.20.0.15", "10.30.0.10", "TCP", 443),
    Packet("EHR app queries database", "10.30.0.10", "10.40.0.10", "TCP", 5432),
    Packet("Doctor tries database directly", "10.20.0.15", "10.40.0.10", "TCP", 5432),
    Packet("Guest Wi-Fi scans EHR", "10.60.0.25", "10.30.0.10", "TCP", 443),
    Packet("Internet opens patient portal", "198.51.100.77", "172.16.10.20", "TCP", 443),
    Packet("Internet tries EHR", "198.51.100.77", "10.30.0.10", "TCP", 443),
]


ZONES = {
    # Clinical workstations used by doctors and nurses.
    "clinical_lan": ip_network("10.20.0.0/24"),
    # Application servers such as the EHR frontend.
    "server_zone": ip_network("10.30.0.0/24"),
    # Database servers with the most sensitive operational data.
    "database_zone": ip_network("10.40.0.0/24"),
    # Network for unmanaged visitor devices.
    "guest_wifi": ip_network("10.60.0.0/24"),
    # Public-facing services separated from the internal network.
    "dmz": ip_network("172.16.10.0/24"),
    # VPN clients after successful remote-access authentication.
    "vpn": ip_network("10.70.0.0/24"),
}


def zone_of(ip):
    # Convert the string into an IP address object.
    candidate = ip_address(ip)
    # Return the first matching named zone.
    for zone_name, network in ZONES.items():
        if candidate in network:
            return zone_name
    # Addresses not in hospital ranges are treated as Internet.
    return "internet"


@dataclass(frozen=True)
class Rule:
    # Short name used in logs.
    name: str
    # Source zone or 'any'.
    src_zone: str
    # Destination zone or 'any'.
    dst_zone: str
    # Protocol or 'any'.
    protocol: str
    # Destination port or 'any'.
    dst_port: int | str
    # Final decision when the rule matches.
    action: str


rules = [
    Rule("allow_clinical_to_ehr_https", "clinical_lan", "server_zone", "TCP", 443, "ALLOW"),
    Rule("allow_ehr_to_database", "server_zone", "database_zone", "TCP", 5432, "ALLOW"),
    Rule("deny_direct_database_access", "clinical_lan", "database_zone", "TCP", 5432, "DENY"),
    Rule("deny_guest_to_internal", "guest_wifi", "any", "any", "any", "DENY"),
    Rule("allow_internet_to_patient_portal", "internet", "dmz", "TCP", 443, "ALLOW"),
    Rule("default_deny", "any", "any", "any", "any", "DENY"),
]


def value_matches(expected, actual):
    # The special value 'any' matches every actual value.
    return expected == "any" or expected == actual


def rule_matches(rule, packet):
    # Calculate the packet zones before comparing the rule.
    src_zone = zone_of(packet.src_ip)
    dst_zone = zone_of(packet.dst_ip)
    # Every relevant field must match.
    return (
        value_matches(rule.src_zone, src_zone)
        and value_matches(rule.dst_zone, dst_zone)
        and value_matches(rule.protocol, packet.protocol)
        and value_matches(rule.dst_port, packet.dst_port)
    )


def evaluate_packet(packet, policy):
    # Try rules in order and stop at the first match.
    for index, rule in enumerate(policy, start=1):
        if rule_matches(rule, packet):
            return {
                "packet": packet.name,
                "src_zone": zone_of(packet.src_ip),
                "dst_zone": zone_of(packet.dst_ip),
                "service": f"{packet.protocol}/{packet.dst_port}",
                "decision": rule.action,
                "matched_rule": index,
                "rule_name": rule.name,
            }
    # A policy should include explicit default deny, but this protects the simulator.
    return {"packet": packet.name, "decision": "DENY", "matched_rule": None, "rule_name": "implicit_deny"}


def flow_key(packet):
    # A flow is identified by endpoints and service in this simplified model.
    return (packet.src_ip, packet.dst_ip, packet.protocol, packet.dst_port)


def reverse_flow_key(packet):
    # A reply reverses source and destination but keeps protocol and service.
    return (packet.dst_ip, packet.src_ip, packet.protocol, packet.dst_port)


def evaluate_stateful(sequence, policy):
    # Store flows that were allowed as new outbound requests.
    established_flows = set()
    rows = []

    for packet in sequence:
        if packet.direction == "reply" and reverse_flow_key(packet) in established_flows:
            rows.append({
                "packet": packet.name,
                "decision": "ALLOW",
                "reason": "established_flow",
            })
            continue

        result = evaluate_packet(packet, policy)
        rows.append({
            "packet": packet.name,
            "decision": result["decision"],
            "reason": result["rule_name"],
        })

        if result["decision"] == "ALLOW" and packet.direction == "new":
            established_flows.add(flow_key(packet))

    return rows


extended_rules = [
    Rule("allow_vpn_to_ehr_https", "vpn", "server_zone", "TCP", 443, "ALLOW"),
    Rule("deny_vpn_to_database", "vpn", "database_zone", "any", "any", "DENY"),
    Rule("allow_clinical_to_ehr_https", "clinical_lan", "server_zone", "TCP", 443, "ALLOW"),
    Rule("allow_ehr_to_database", "server_zone", "database_zone", "TCP", 5432, "ALLOW"),
    Rule("deny_direct_database_access", "clinical_lan", "database_zone", "TCP", 5432, "DENY"),
    Rule("deny_guest_to_internal", "guest_wifi", "any", "any", "any", "DENY"),
    Rule("allow_internet_to_patient_portal", "internet", "dmz", "TCP", 443, "ALLOW"),
    Rule("deny_dmz_to_database", "dmz", "database_zone", "any", "any", "DENY"),
    Rule("default_deny", "any", "any", "any", "any", "DENY"),
]
'''


notebook = {
    "cells": [
        md(
            """
# Firewall Policy Simulator

This notebook models a small hospital network. It is not a real firewall and it does not protect
your computer. The goal is to make firewall decisions visible: packets enter, rules are evaluated
in order, a decision is made, and a log entry explains why.

The running scenario is **St. Isidore Hospital**:

- clinical workstations use the EHR web application;
- the EHR application server talks to the EHR database;
- guest Wi-Fi must not reach internal systems;
- remote clinicians enter through a VPN zone;
- public users reach only the patient portal in the DMZ.
"""
        ),
        code(common_code),
        md(
            """
## 1. Represent Network Packets

A firewall does not see a sentence such as "a doctor is opening the patient record".
At packet-filtering level, it sees fields such as source IP, destination IP, protocol, and port.
"""
        ),
        code(
            """
show_table([packet.__dict__ for packet in packets])
"""
        ),
        md(
            """
## 2. Define Hospital Zones

The firewall policy becomes easier to read if raw addresses are grouped into zones.
This mirrors real network design: clinical LAN, server zone, database zone, guest Wi-Fi, DMZ, VPN,
and Internet.
"""
        ),
        code(
            """
for packet in packets:
    print(f"{packet.name}: {zone_of(packet.src_ip)} -> {zone_of(packet.dst_ip)}")
"""
        ),
        md(
            """
## 3. Build an Ordered Firewall Policy

Rules are evaluated from top to bottom. The first matching rule decides the result.
This is why a firewall policy is an ordered decision procedure, not just a checklist.
"""
        ),
        code(
            """
show_table([rule.__dict__ for rule in rules])
"""
        ),
        code(
            """
log = [evaluate_packet(packet, rules) for packet in packets]
show_table(log)
"""
        ),
        md(
            """
## 4. Experiment: Rule Order Matters

The next policy contains a mistake: a broad allow rule appears before the narrow deny rule.
The doctor's workstation can now reach the database directly.
"""
        ),
        code(
            """
bad_rules = [
    Rule("bad_allow_clinical_to_any_database_port", "clinical_lan", "database_zone", "TCP", 5432, "ALLOW"),
    Rule("deny_direct_database_access", "clinical_lan", "database_zone", "TCP", 5432, "DENY"),
    Rule("default_deny", "any", "any", "any", "any", "DENY"),
]

test_packet = Packet("Doctor tries database directly", "10.20.0.15", "10.40.0.10", "TCP", 5432)

show_table([
    evaluate_packet(test_packet, bad_rules),
    evaluate_packet(test_packet, rules),
])
"""
        ),
        md(
            """
## 5. Add Stateful Behavior

A stateless firewall evaluates every packet independently. A stateful firewall remembers allowed
flows, so a reply packet can be accepted because it belongs to an established connection.
"""
        ),
        code(
            """
conversation = [
    Packet("Doctor request to EHR", "10.20.0.15", "10.30.0.10", "TCP", 443, "new"),
    Packet("EHR reply to doctor", "10.30.0.10", "10.20.0.15", "TCP", 443, "reply"),
]

show_table(evaluate_stateful(conversation, rules))
"""
        ),
        md(
            """
## 6. Add VPN and DMZ Decisions

VPN access should not mean full internal access. A DMZ service should be reachable from the Internet,
but it should not freely reach the database zone.
"""
        ),
        code(
            """
vpn_and_dmz_tests = [
    Packet("Remote doctor opens EHR over VPN", "10.70.0.42", "10.30.0.10", "TCP", 443),
    Packet("Remote doctor tries database", "10.70.0.42", "10.40.0.10", "TCP", 5432),
    Packet("Internet opens patient portal", "198.51.100.77", "172.16.10.20", "TCP", 443),
    Packet("Compromised portal tries database", "172.16.10.20", "10.40.0.10", "TCP", 5432),
]

show_table([evaluate_packet(packet, extended_rules) for packet in vpn_and_dmz_tests])
"""
        ),
        md(
            """
## 7. Analyze Firewall Logs

The log is evidence. It can show whether policy is working, where blocked traffic comes from, and
which systems repeatedly attempt suspicious connections.
"""
        ),
        code(
            """
all_tests = packets + vpn_and_dmz_tests
firewall_log = [evaluate_packet(packet, extended_rules) for packet in all_tests]

# Count allow/deny decisions by source zone.
counts = {}
for row in firewall_log:
    key = (row["src_zone"], row["decision"])
    counts[key] = counts.get(key, 0) + 1

summary = [
    {"src_zone": src_zone, "decision": decision, "events": events}
    for (src_zone, decision), events in sorted(counts.items())
]

show_table(summary)
"""
        ),
        code(
            """
# Show only denied events, because they often deserve operational review.
show_table([row for row in firewall_log if row["decision"] == "DENY"])
"""
        ),
        md(
            """
## Reflection Questions

1. Which allowed flows are necessary for patient care?
2. Which denied flows represent useful containment?
3. What would change if the patient portal also needed to read appointment data?
4. Which rules would you monitor most closely in a real hospital?
5. Where would a real system add identity, patching, endpoint protection, and encryption controls?
"""
        ),
    ],
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}


output_path = Path(__file__).with_name("01_firewall_policy_simulator.ipynb")
output_path.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
print(f"Wrote {output_path}")

script_path = Path(__file__).with_name("firewall_policy_simulator.py")
script_path.write_text(
    common_code
    + r'''

if __name__ == "__main__":
    print("\nHospital zones")
    for packet in packets:
        print(f"{packet.name}: {zone_of(packet.src_ip)} -> {zone_of(packet.dst_ip)}")

    print("\nBaseline firewall decisions")
    show_table([evaluate_packet(packet, rules) for packet in packets])

    print("\nRule-order experiment")
    bad_rules = [
        Rule("bad_allow_clinical_to_any_database_port", "clinical_lan", "database_zone", "TCP", 5432, "ALLOW"),
        Rule("deny_direct_database_access", "clinical_lan", "database_zone", "TCP", 5432, "DENY"),
        Rule("default_deny", "any", "any", "any", "any", "DENY"),
    ]
    test_packet = Packet("Doctor tries database directly", "10.20.0.15", "10.40.0.10", "TCP", 5432)
    show_table([evaluate_packet(test_packet, bad_rules), evaluate_packet(test_packet, rules)])

    print("\nStateful replies")
    conversation = [
        Packet("Doctor request to EHR", "10.20.0.15", "10.30.0.10", "TCP", 443, "new"),
        Packet("EHR reply to doctor", "10.30.0.10", "10.20.0.15", "TCP", 443, "reply"),
    ]
    show_table(evaluate_stateful(conversation, rules))

    print("\nVPN and DMZ decisions")
    vpn_and_dmz_tests = [
        Packet("Remote doctor opens EHR over VPN", "10.70.0.42", "10.30.0.10", "TCP", 443),
        Packet("Remote doctor tries database", "10.70.0.42", "10.40.0.10", "TCP", 5432),
        Packet("Internet opens patient portal", "198.51.100.77", "172.16.10.20", "TCP", 443),
        Packet("Compromised portal tries database", "172.16.10.20", "10.40.0.10", "TCP", 5432),
    ]
    show_table([evaluate_packet(packet, extended_rules) for packet in vpn_and_dmz_tests])
''',
    encoding="utf-8",
)
print(f"Wrote {script_path}")
