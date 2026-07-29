# Lesson 03 Notebooks

These notebooks are toy examples for teaching access-control concepts. They are not production
implementations and should not be used as security libraries.

Real operating systems, databases, identity providers, EHR platforms, and cloud services usually
provide their own access-control mechanisms. System administrators and security teams normally
decide the policy to apply: roles, permissions, labels, delegation rules, exceptions, review
processes, and audit requirements.

The notebooks use the same St. Isidore Hospital users and resources to compare how decisions change
under different models:

- `01_dac_toy_model.ipynb`: DAC with an access matrix, ACL view, and delegation.
- `02_mac_toy_model.ipynb`: MAC with labels, clearances, ranks, and compartments.
- `03_rbac_toy_model.ipynb`: RBAC with users, roles, permissions, sessions, and separation of duty.
- `04_compare_models.ipynb`: side-by-side comparison of DAC, MAC, and RBAC decisions.

Run them with any Python 3 Jupyter kernel. They use only the Python standard library.
