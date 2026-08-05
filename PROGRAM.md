COURSE: Healthcare Data Privacy and Security

OVERVIEW: This course introduces students and healthcare professionals to the
principles, policies, and technologies used to protect health data in digital
systems. The course combines security foundations, cryptography, authentication,
access control, networking, operational security, and privacy regulation through a
running hospital scenario and applied labs.

Learners will develop practical competence to reason about healthcare data
risks, design appropriate safeguards, operate basic security controls, understand
privacy duties, and respond to incidents that affect patient data and care
continuity.

SCHEDULE: 9 lessons, 3.5 hours each

RUNNING SCENARIO: St. Isidore Hospital

The course repeatedly returns to the same fictional hospital environment:
clinical workstations, laboratory systems, patient records, OpenHospital,
remote access, guest networks, backups, logs, and privacy obligations.


LESSON 1: Foundations of Computer Security in Healthcare

- Why healthcare security matters
- Confidentiality, integrity, and availability
- Risk, likelihood, impact, and basic risk matrices
- Threats, vulnerabilities, attacks, and attack surfaces
- Security objectives in a hospital environment
- Running example: St. Isidore Hospital and its systems

Outcome: learners can describe security goals and risks for a healthcare system.


LESSON 2: Cryptographic Foundations for Healthcare Systems

- Classical encryption as intuition
- Symmetric encryption: DES, 3DES, AES
- Block ciphers, stream ciphers, and modes of operation
- Authenticated encryption and AES-GCM
- Hash functions, MACs, HMAC, and password hashing
- Public-key cryptography, RSA, signatures, certificates, and key exchange
- Key management and randomness
- Python notebooks with concrete examples

Outcome: learners understand what cryptographic tools do, what they do not do,
and where they fit in healthcare systems.


LESSON 3: Access Control in Healthcare Systems

- Authentication, authorization, and audit
- Subjects, objects, rights, and policies
- Discretionary Access Control (DAC)
- Mandatory Access Control (MAC)
- Role-Based Access Control (RBAC)
- Least privilege, separation of duties, and emergency access
- Python notebooks comparing DAC, MAC, and RBAC toy models

Outcome: learners can design and compare access-control policies for hospital
workflows.


LESSON 4: RBAC and Logging in OpenHospital

- Deploy and access OpenHospital
- Understand users, groups, and permissions
- Configure realistic RBAC policies
- Test access with different hospital roles
- Inspect logs and identify audit gaps
- Discuss why real systems implement access models differently from toy models

Outcome: learners can operate a real healthcare application enough to configure
and verify access-control behavior.


LESSON 5: Authentication in Healthcare Systems

- Authentication factors
- Password files and password storage
- Password attacks and password policy
- Challenge-response authentication
- Tokens, smart cards, remote authentication, and MFA
- One-time passwords and TOTP
- Python notebooks on password hashing, challenge-response, and MFA

Outcome: learners understand common authentication mechanisms and the risks of
weak authentication in healthcare environments.


LESSON 6: Basic Networking and Firewalls

- Networking foundations: IP, subnets, ports, DNS, routing
- Hospital network architecture
- Firewalls, packet filtering, stateful firewalls, and proxy firewalls
- Allow-list and deny-list thinking
- VPNs and secure remote access
- Deployment patterns for healthcare systems
- Hands-on firewall policy simulation
- Optional: cloud computing concepts and risks

Outcome: learners can reason about network segmentation and firewall policy in a
hospital environment.


LESSON 7: OpenHospital API Network Security Lab

- Deploy the real OpenHospital API with MariaDB
- Place Nginx in front of the API
- Start from an intentionally open proxy baseline
- Test health checks, Swagger, login, CRUD endpoints, and verified reads
- Harden the proxy by subnet and API path
- Verify clinical, lab, VPN, guest, and DMZ behavior
- Inspect proxy and backend logs
- Use real CRUD where supported and real demo-data reads where clinical workflow
  constraints make fake writes inappropriate

Outcome: learners can deploy and test a realistic healthcare API security
architecture with network-based access restrictions.


LESSON 8: Healthcare Privacy and Data Protection

- From privacy as private life to data protection as information governance
- Decision privacy and information privacy
- Personal data, medical data, PHI, identifiability
- Anonymization and pseudonymization
- GDPR as an influential reference model, not the only global regime
- Global healthcare privacy frameworks: GDPR, HIPAA, CCPA/CPRA, POPIA, APEC
- GDPR concepts: controller, processor, processing, principles, legal bases
- Consent and its limits in healthcare
- Patient rights: information, access, rectification, erasure, portability,
  objection, automated decisions
- Accountability, data protection by design/default, DPIA, breach duties, DPO
- Privacy risks in digital healthcare and links to previous security lessons

Outcome: learners can connect technical safeguards with legal and ethical duties
around patient data.


LESSON 9: Operational Security, Ransomware, and Incident Response

- Operational security mindset
- Governance, identify, protect, detect, respond, recover
- Phishing, scams, fake IT support, invoice fraud, MFA fatigue
- Ransomware attack chain and healthcare impact
- Prevention and early warning signs
- Backups, 3-2-1 strategy, immutable/offline copies
- RPO, RTO, restore testing, and downtime procedures
- Incident response lifecycle
- Breach triage and incident communication
- Tabletop exercise: St. Isidore ransomware on Monday morning

Outcome: learners can describe practical actions before, during, and after a
healthcare security incident.


COURSE INTEGRATION

The course intentionally moves from concepts to mechanisms, then to real systems
and operational response:

1. Security goals and risk
2. Encryption and integrity mechanisms
3. Access-control models
4. Real OpenHospital RBAC configuration
5. Authentication mechanisms and attacks
6. Networking and firewall policy
7. Real OpenHospital API proxy lab
8. Privacy and data protection governance
9. Ransomware, backups, incident response, and communication


LABS AND PRACTICAL MATERIAL

- Cryptography notebooks
- DAC/MAC/RBAC notebooks
- Authentication notebooks
- Firewall simulation notebook
- OpenHospital RBAC lab
- OpenHospital API network/proxy lab
- Operational tabletop exercise


OPTIONAL EXTENSIONS

- Health information systems and interoperability: EHR, LIS, RIS, PACS,
  DHIS2, HL7/FHIR
- Standards and frameworks: ISO 27001, NIST, CIS Controls
- AI and health data: privacy-preserving analytics, model governance,
  inference risks, synthetic data, federated learning
- Medical devices, wearables, mobile health, and telemedicine security
