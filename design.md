
# Goal
The goal of this project is to develop a Python application
that can synchronize issues between a GitHub repository and a Jira project.
The application should be able to perform the following tasks:

* Retrieve issues from GitHub and Jira
* Keep track of what issues have been synced
* Handle outages or downtime of either platform
* Handle conflicts if changes are made to both platforms

# Functional Requirements:

- Authentication: The application must be able to authenticate with both the GitHub and Jira APIs to retrieve data and make changes.
- Configuration: The application shall allow for configuration of the following parameters:
    - GitHub repository and Jira project names/URLs 
    - Synchronization schedule
- Issue Retrieval: The application should be able to retrieve issues from both platforms using their respective APIs.
- Issue Comparison: The application should compare the issues from both platforms to identify which ones need to be synced.
- Conflict Resolution: The application should be able to handle conflicts when changes are made to the same issue on both platforms.
- Sync Tracking: The application should keep track of which issues have been synced and when they were last synced.

# Non-functional Requirements:

- Performance: The application should be able to handle 50 updated (or newly created) issues per day  without slowing down or crashing.
- Reliability: The application should be able to handle outages or downtime of either platform and resume syncing when the platforms are back online.
- Security: The application should ensure that sensitive information such as authentication credentials are securely stored and transmitted.

# Acceptance Criteria:

1. (done) The application shall successfully retrieve changes in issues from both the GitHub repository and Jira project.
2. (done) The application shall be able to authenticate with both the GitHub and Jira APIs.
3. (done) The application shall provide configuration options for the GitHub/Jira names/URLs/credentials.
4. (done) The application shall successfully compare changes in issues between the two systems.
   1. Note: This is not a full comparison of all attributes, but rather a comparison of the attributes that are relevant to the sync.
5. (done) The application shall successfully update issues from Github in Jira
6. (non goal) The application shall successfully update issues in both the GitHub repository and Jira project.
7. (done) The application shall keep track of what issues are synced between the two systems.
8. (done) The application shall work on a configurable schedule.
   1. Note: rely on external scheduler (cron, Super Collider Data Jobs)
9. (non goal) The application shall provide configurable mappings of attributes between the two systems.
10. (todo) Create some cicd to run tests and deploy the application (python distribution) in pypi .
11. (non goal) The application shall consolidate changes in issues if there are changes on both systems.
12. (todo: testing) The application shall be able to handle 50 updated (or newly created) issues per day without slowing down or crashing.
13. (todo: testing) The application shall be able to handle outages or downtime of either platform and resume syncing when the platforms are back online.
14. (not goal) The application shall be able to handle conflicts when changes are made to the same issue on both platforms.
    1. Note: There are SyncStrategy that can be extended with other conflict resolution logic. Currently it's github overwrites jira.
15. (todo) Create python package that can be installed and used as a library
16. (todo) create data job that can be used to run the sync application 
    
# Architecture


The GitHub-Jira Issue Sync Application will be built using the following architecture:

- Python 3.x
- GitHub API
- Jira API
- Scheduled jobs using cron or similar scheduler (possibly Super Collider Data Jobs)

The application will consist of those main components:

1. GitHub Issue Connection to interact with the GitHub repository and retrieve relevant issue data.
2. Jira Issue Connection to interact with the Jira project and retrieve relevant issue data.
3. Sync Engine module that manages the synchronization of issues between the two platforms.
4. Database to store stateful data (Database is a generic term, it can be VDK Properties API, File storage, etc.)


![sync diagram](https://www.plantuml.com/plantuml/svg/ZP31JiCm38RlVWfhTrvW1pGnq0Q2qxG7S9keYzewaUC88SIx4pT50h73UhB_VFd_lzbb9T4oJv37m8c4PkpZd29xLlm4hDz35ETb7wSes4tKZqsjmo2ni6idxvUW7hu0gDUwdhCNI2GQ-f285JSlGGYVSouUtoA72csGCffSzx_i8UYnT5Vem_4VU_hW7fzu2EmNn7PmfDHHzlYu3W3M2E_kcyKMz-99VSRQjIItZCGObiJ8s1h00jijSztYoRFBAsGHOB8T_yHKHADKhvbI2ZmWiRl6hoLUOnnppRUuI-b-apScj_Sph_Fw5oOq47RrKfcdRm00)
