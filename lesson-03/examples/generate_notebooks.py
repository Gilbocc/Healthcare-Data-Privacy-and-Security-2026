import json
from pathlib import Path


root = Path(__file__).parent


def md(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.strip().splitlines()],
    }


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.strip().splitlines()],
    }


def write_notebook(filename: str, title: str, cells: list[dict]) -> None:
    notebook = {
        "cells": [md(f"# {title}")] + cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "pygments_lexer": "ipython3",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (root / filename).write_text(json.dumps(notebook, indent=2), encoding="utf-8")


shared_setup = """
from dataclasses import dataclass
from pprint import pprint


@dataclass(frozen=True)
class Request:
    user: str
    operation: str
    resource: str
    context: dict


users = {
    "dr_rossi": {"name": "Dr. Rossi", "department": "cardiology"},
    "nurse_amina": {"name": "Nurse Amina", "department": "ward-a"},
    "lab_tech": {"name": "Lab Technician", "department": "laboratory"},
    "billing_clerk": {"name": "Billing Clerk", "department": "billing"},
    "privacy_auditor": {"name": "Privacy Auditor", "department": "compliance"},
}

resources = {
    "ehr_note_42": {"type": "ehr_note", "patient": "patient-42", "department": "cardiology"},
    "lab_result_42": {"type": "lab_result", "patient": "patient-42", "department": "laboratory"},
    "billing_record_42": {"type": "billing_record", "patient": "patient-42", "department": "billing"},
    "audit_log": {"type": "audit_log", "patient": None, "department": "compliance"},
}

requests = [
    Request("dr_rossi", "read", "ehr_note_42", {"assigned_patient": True, "emergency": False}),
    Request("nurse_amina", "write", "ehr_note_42", {"assigned_patient": True, "emergency": False}),
    Request("lab_tech", "write", "lab_result_42", {"assigned_patient": False, "emergency": False}),
    Request("billing_clerk", "read", "ehr_note_42", {"assigned_patient": False, "emergency": False}),
    Request("privacy_auditor", "read", "audit_log", {"assigned_patient": False, "emergency": False}),
]
"""


write_notebook(
    "01_dac_toy_model.ipynb",
    "DAC Toy Model: Access Matrix, ACLs, and Delegation",
    [
        md(
            """
## Teaching goal

This is a toy model of Discretionary Access Control (DAC). It shows how access can be represented
with an access matrix, then viewed as object-centered ACLs. Real operating systems, databases, and
healthcare applications already provide mature DAC or ACL mechanisms; system administrators normally
configure policy instead of implementing the enforcement engine themselves.
"""
        ),
        code(shared_setup),
        code(
            """
# The access matrix maps each user to each resource and the operations allowed there.
access_matrix = {
    "dr_rossi": {
        "ehr_note_42": {"read", "write"},
        "lab_result_42": {"read"},
    },
    "nurse_amina": {
        "ehr_note_42": {"read", "write"},
        "lab_result_42": {"read"},
    },
    "lab_tech": {
        "lab_result_42": {"read", "write"},
    },
    "billing_clerk": {
        "billing_record_42": {"read", "write"},
    },
    "privacy_auditor": {
        "audit_log": {"read"},
    },
}


def dac_allows(request: Request) -> bool:
    # DAC checks the requesting identity and the rights assigned to that identity.
    user_rights = access_matrix.get(request.user, {})
    resource_rights = user_rights.get(request.resource, set())
    return request.operation in resource_rights


for request in requests:
    print(request.user, request.operation, request.resource, "=>", dac_allows(request))
"""
        ),
        code(
            """
# The same matrix can be viewed as ACLs: each resource lists who may do what.
def build_acls(matrix):
    acls = {}
    for user, resource_map in matrix.items():
        for resource, operations in resource_map.items():
            acls.setdefault(resource, {})[user] = sorted(operations)
    return acls


acls = build_acls(access_matrix)
pprint(acls)
"""
        ),
        code(
            """
# DAC can allow delegation: someone with enough control may share access.
def delegate(owner: str, grantee: str, resource: str, operations: set[str]) -> None:
    # In a real system this delegation would itself be authorized and audited.
    if "write" not in access_matrix.get(owner, {}).get(resource, set()):
        raise PermissionError(f"{owner} cannot delegate access to {resource}")
    access_matrix.setdefault(grantee, {}).setdefault(resource, set()).update(operations)


print("Before delegation:", dac_allows(Request("billing_clerk", "read", "ehr_note_42", {})))
delegate("dr_rossi", "billing_clerk", "ehr_note_42", {"read"})
print("After delegation:", dac_allows(Request("billing_clerk", "read", "ehr_note_42", {})))
"""
        ),
        md(
            """
## What to notice

DAC is flexible, especially for collaboration. The risk is that access can spread if delegation is
not controlled. In production, administrators define sharing rules, ownership rules, and audit
expectations; they do not hand-code an access matrix inside an application notebook.
"""
        ),
    ],
)


write_notebook(
    "02_mac_toy_model.ipynb",
    "MAC Toy Model: Labels, Clearances, and Compartments",
    [
        md(
            """
## Teaching goal

This is a toy model of Mandatory Access Control (MAC). It compares subject clearances with object
labels. Real MAC systems are implemented by operating systems, database engines, or specialized
platforms. Administrators choose labels, compartments, and policy rules.
"""
        ),
        code(shared_setup),
        code(
            """
# Rank increases with sensitivity.
ranks = {
    "public": 0,
    "internal": 1,
    "confidential": 2,
    "restricted": 3,
}

# A clearance combines a rank with the compartments the subject belongs to.
clearances = {
    "dr_rossi": {"rank": "restricted", "compartments": {"cardiology"}},
    "nurse_amina": {"rank": "confidential", "compartments": {"ward-a", "cardiology"}},
    "lab_tech": {"rank": "confidential", "compartments": {"laboratory"}},
    "billing_clerk": {"rank": "internal", "compartments": {"billing"}},
    "privacy_auditor": {"rank": "restricted", "compartments": {"compliance", "cardiology", "laboratory"}},
}

# A label defines the sensitivity and compartment required by the resource.
labels = {
    "ehr_note_42": {"rank": "confidential", "compartments": {"cardiology"}},
    "lab_result_42": {"rank": "confidential", "compartments": {"laboratory"}},
    "billing_record_42": {"rank": "internal", "compartments": {"billing"}},
    "audit_log": {"rank": "restricted", "compartments": {"compliance"}},
}
"""
        ),
        code(
            """
def dominates(clearance: dict, label: dict) -> bool:
    # Rank must be high enough.
    rank_ok = ranks[clearance["rank"]] >= ranks[label["rank"]]

    # The subject must have every compartment required by the object.
    compartments_ok = label["compartments"].issubset(clearance["compartments"])

    return rank_ok and compartments_ok


def mac_allows(request: Request) -> bool:
    # This toy rule focuses on read access; real MAC models also constrain writes.
    if request.operation != "read":
        return False
    return dominates(clearances[request.user], labels[request.resource])


for request in requests:
    print(request.user, request.operation, request.resource, "=>", mac_allows(request))
"""
        ),
        code(
            """
# Changing a label changes the decision even when user identity stays the same.
request = Request("dr_rossi", "read", "ehr_note_42", {})
print("Before relabel:", mac_allows(request))

labels["ehr_note_42"] = {"rank": "restricted", "compartments": {"psychiatry"}}
print("After relabel:", mac_allows(request))

# Restore the original label for later experimentation.
labels["ehr_note_42"] = {"rank": "confidential", "compartments": {"cardiology"}}
"""
        ),
        md(
            """
## What to notice

MAC is less about personal sharing and more about centrally enforced information flow. A user with a
valid account and a senior job title can still be denied if the clearance does not dominate the
resource label.
"""
        ),
    ],
)


write_notebook(
    "03_rbac_toy_model.ipynb",
    "RBAC Toy Model: Users, Roles, Permissions, and Sessions",
    [
        md(
            """
## Teaching goal

This is a toy model of Role-Based Access Control (RBAC). It shows how permissions are assigned to
roles, users are assigned to roles, and sessions activate only the roles needed for a task. Real EHRs,
identity platforms, and operating systems provide RBAC features; administrators usually design the
roles, permissions, constraints, and review process.
"""
        ),
        code(shared_setup),
        code(
            """
# Users may be assigned multiple roles.
user_roles = {
    "dr_rossi": {"attending_physician", "researcher"},
    "nurse_amina": {"ward_nurse"},
    "lab_tech": {"lab_technician"},
    "billing_clerk": {"billing_staff"},
    "privacy_auditor": {"auditor"},
}

# Roles carry permissions. A permission is represented as (operation, resource_type).
role_permissions = {
    "attending_physician": {("read", "ehr_note"), ("write", "ehr_note"), ("read", "lab_result")},
    "ward_nurse": {("read", "ehr_note"), ("write", "ehr_note"), ("read", "lab_result")},
    "lab_technician": {("read", "lab_result"), ("write", "lab_result")},
    "billing_staff": {("read", "billing_record"), ("write", "billing_record")},
    "auditor": {("read", "audit_log")},
    "researcher": {("read", "deidentified_dataset")},
}

# A session activates a subset of assigned roles.
active_sessions = {
    "clinical_shift": {"dr_rossi": {"attending_physician"}},
    "research_session": {"dr_rossi": {"researcher"}},
}
"""
        ),
        code(
            """
def rbac_allows(request: Request, session_name: str) -> bool:
    # Only roles active in this session can be used.
    active_roles = active_sessions.get(session_name, {}).get(request.user, set())

    # Activated roles must also be assigned to the user.
    assigned_roles = user_roles.get(request.user, set())
    valid_active_roles = active_roles.intersection(assigned_roles)

    # Check whether any active role grants the requested operation on this resource type.
    resource_type = resources[request.resource]["type"]
    needed_permission = (request.operation, resource_type)
    return any(needed_permission in role_permissions[role] for role in valid_active_roles)


for request in requests:
    print(request.user, request.operation, request.resource, "=>", rbac_allows(request, "clinical_shift"))
"""
        ),
        code(
            """
# Changing active roles changes the decision without changing the user's identity.
clinical_request = Request("dr_rossi", "read", "ehr_note_42", {})
print("Clinical session:", rbac_allows(clinical_request, "clinical_shift"))
print("Research session:", rbac_allows(clinical_request, "research_session"))
"""
        ),
        code(
            """
# Dynamic separation of duty can block unsafe role combinations in one session.
conflicting_roles = [{"attending_physician", "researcher"}]


def session_is_allowed(active_roles: set[str]) -> bool:
    # A session is denied if it activates any forbidden combination.
    return not any(conflict.issubset(active_roles) for conflict in conflicting_roles)


candidate_roles = {"attending_physician", "researcher"}
print("Can activate both roles together?", session_is_allowed(candidate_roles))
"""
        ),
        md(
            """
## What to notice

RBAC is often the most intuitive model for hospitals because it follows job responsibilities.
The important administrative work is policy design: defining roles, avoiding role explosion,
reviewing assignments, and enforcing constraints such as separation of duty.
"""
        ),
    ],
)


write_notebook(
    "04_compare_models.ipynb",
    "Comparing DAC, MAC, and RBAC on the Same Requests",
    [
        md(
            """
## Teaching goal

This notebook puts the three toy models side by side. The same request may be allowed in one model
and denied in another because each model asks a different policy question.
"""
        ),
        code(shared_setup),
        code(
            """
# Minimal DAC policy.
dac_matrix = {
    "dr_rossi": {"ehr_note_42": {"read", "write"}},
    "nurse_amina": {"ehr_note_42": {"read", "write"}},
    "lab_tech": {"lab_result_42": {"read", "write"}},
    "billing_clerk": {"billing_record_42": {"read", "write"}},
    "privacy_auditor": {"audit_log": {"read"}},
}

# Minimal MAC policy.
ranks = {"internal": 1, "confidential": 2, "restricted": 3}
clearances = {
    "dr_rossi": {"rank": "restricted", "compartments": {"cardiology"}},
    "nurse_amina": {"rank": "confidential", "compartments": {"ward-a", "cardiology"}},
    "lab_tech": {"rank": "confidential", "compartments": {"laboratory"}},
    "billing_clerk": {"rank": "internal", "compartments": {"billing"}},
    "privacy_auditor": {"rank": "restricted", "compartments": {"compliance", "cardiology"}},
}
labels = {
    "ehr_note_42": {"rank": "confidential", "compartments": {"cardiology"}},
    "lab_result_42": {"rank": "confidential", "compartments": {"laboratory"}},
    "billing_record_42": {"rank": "internal", "compartments": {"billing"}},
    "audit_log": {"rank": "restricted", "compartments": {"compliance"}},
}

# Minimal RBAC policy.
user_roles = {
    "dr_rossi": {"attending_physician"},
    "nurse_amina": {"ward_nurse"},
    "lab_tech": {"lab_technician"},
    "billing_clerk": {"billing_staff"},
    "privacy_auditor": {"auditor"},
}
role_permissions = {
    "attending_physician": {("read", "ehr_note"), ("write", "ehr_note"), ("read", "lab_result")},
    "ward_nurse": {("read", "ehr_note"), ("write", "ehr_note"), ("read", "lab_result")},
    "lab_technician": {("read", "lab_result"), ("write", "lab_result")},
    "billing_staff": {("read", "billing_record"), ("write", "billing_record")},
    "auditor": {("read", "audit_log")},
}
"""
        ),
        code(
            """
def dac(request):
    return request.operation in dac_matrix.get(request.user, {}).get(request.resource, set())


def mac(request):
    # This toy MAC function allows reads only, to keep the example focused.
    if request.operation != "read":
        return False
    clearance = clearances[request.user]
    label = labels[request.resource]
    rank_ok = ranks[clearance["rank"]] >= ranks[label["rank"]]
    compartments_ok = label["compartments"].issubset(clearance["compartments"])
    return rank_ok and compartments_ok


def rbac(request):
    resource_type = resources[request.resource]["type"]
    needed_permission = (request.operation, resource_type)
    return any(
        needed_permission in role_permissions[role]
        for role in user_roles.get(request.user, set())
    )


for request in requests:
    print(f"{request.user:16} {request.operation:5} {request.resource:18}",
          "DAC=", dac(request),
          "MAC=", mac(request),
          "RBAC=", rbac(request))
"""
        ),
        code(
            """
# Try changing one policy and rerun the comparison.
# Example: give billing staff read access to EHR notes in RBAC.
role_permissions["billing_staff"].add(("read", "ehr_note"))

request = Request("billing_clerk", "read", "ehr_note_42", {"assigned_patient": False})
print("After RBAC policy change:")
print("DAC=", dac(request), "MAC=", mac(request), "RBAC=", rbac(request))
"""
        ),
        md(
            """
## What to notice

The model changes the question:

- DAC asks: did this identity receive this right on this object?
- MAC asks: does the subject clearance dominate the object label?
- RBAC asks: does an active/assigned role grant this operation?

Real systems provide the enforcement mechanisms. Administrators and security teams decide the
policies, review them, and align them with clinical workflow and legal duties.
"""
        ),
    ],
)


print(f"Wrote notebooks in {root}")
