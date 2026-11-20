# IQAC Activity Tracking System — Project Definition and SRS v1.0

## 1. Project Identification

| Item | Details |
| --- | --- |
| Project Name | IQAC Activity Tracking System |
| Project Type | Web-based system for planning, tracking and reporting IQAC activities |
| Team ID | T096 |
| Team Members | Shivam Sharma, Garv Jain, Dipanshu Soni, Manas Gupta |
| Roll Numbers | 24UCS269, 24UCS270, 24UCS271, 24UCS272 |
| Development Model | Agile + Incremental Development |
| Primary Users | IQAC Coordinator and members, Department Quality Coordinators, Faculty/Staff, Students, Administrators |
| Development Team | Student software development team |
| Course | Software Engineering |
| Project Objective | To build a centralised system where every IQAC activity including its owner, deadline, evidence and outcome are recorded and monitored |
| Expected Outcome | A working, tested and documented web system, built in increments, that shows the live status of all IQAC activities and can export criterion-wise reports |

## 2. Project Background

**Current Problem**

Internal Quality Assurance Cell (IQAC) plans and tests implementations of quality related work through feedback collections, academic and administrative audits, workshops, documentations and then collect proofs of all of it for the Annual Quality Assurance Report.

Most of this work runs on Excel sheets, WhatsApp groups, email threads, shared drives, google forms etc, which results in a cluttered form of available information and not a centra.ised database for all users that acts as a major problem.

The usual problems are:

- No proper accountability of a particular problem.

- Deadlines are tracked in one file and progress in another which remains out of sync.

- Evidence (photos, attendance sheets, notices, reports) sits in personal drives, folders or in cluttered forms, collecting all becomes a serious problem.

- There is no single screen that tells the pending work or the completion dashboard.

- Multiple times repetition of similar information.

**Proposed Solution**

The IQAC Activity Tracking System tracks all at one place. A coordinator creates an activity, assigns it to a department, sets a deadline and tags it to the quality area it belongs. The assigned person updates progress, uploads evidence and records the outcome when it is done. Students can also answer feedback form and many similar forms.

## 3. Project Vision

To give the department one reliable place where the whole activity that can be tracked by administrators and easy interface for the students, and ultimately removing the need to import evidence from different format to one.

## 4. Problem Statement

IQAC work is spread across many departments and many users, and its value depends almost entirely on evidence collected. When activities are tracked through separate files and informal messages, things might go wrong: ownership becomes unclear, deadlines slip without anyone noticing, evidence gets missing or scattered. There is currently no single system that links an activity to its owner, its deadline, its status, its supporting documents and its final outcome.

## 5. Project Objective:

The initial objectives are:

1. To provide one central place where all IQAC activities are tracked.

2. To let authorised coordinators create activities and assign each to a responsible department.

3. To let every activity be tagged to the quality domain so reports can be grouped later.

4. To set deadlines and clearly show which activities are due and which are overdue.

5. To let responsible users upload supporting evidence files against the activity itself.

6. To record the outcome of an activity once it is finished.

7. To send reminders before a deadline and after it is missed.

8. To control their access by role (admin access).

## 6. Stakeholders

| Stakeholder | Interest / Role |
| --- | --- |
| IQAC Coordinator | Plans activities, monitors overall progress, prepares reports |
| IQAC Members | Review activity status and verify submitted evidence |
| Department and Quality Coordinators | Create and manage activities for their department |
| Administrator | Manage users, roles and overall system |
| Faculty / Staff | Complete assigned activities and upload evidence |
| Heads of Department | Monitor activities belonging to their department |
| University/Institute | Gets a summary view of quality work and reports |
| Students | Filling feedback form |
| Development team | — |

## 7. Initial Scope

The first version will cover:

- User registration and login

- Role-based access control

- Creating an IQAC activity

- Assigning an activity to a person or department

- Tagging an activity to a domain area

- Setting deadlines

- Updating status and progress

- Uploading and storing files

- Recording the outcome of a completed activity

- Verification of evidence by an IQAC member

- Searching and filtering activities

- Deadline reminders and notifications

- Dashboard for IQAC members

- Basic reports with export

- Activity history log

**Initially Out of Scope**

To keep the project realistic for one semester, the following are excluded from the first version:

- Full college ERP functionality

- Payment handling

- Student attendance management

- Online examination

- Hostel, transport and payroll modules

- Automatic generation of the complete AQAR document in NAAC's own format

- Direct integration with NAAC or university portals

- AI-based suggestions or predictions

- Mobile application

## 8. Initial Assumptions

- Users will have internet access.

- Users will have valid institutional login credentials.

- The institute already has some defined list of domain areas

- Every activity will have one clearly identified responsible person or department.

- Every activity will have a deadline.

- Only authorised users will create or modify activities.

- Responsible users will upload evidence themselves. the system will not fetch it from anywhere.

- Uploaded evidence will be in common formats such as PDF, DOCX, JPG or PNG.

- The system will be built as a web application with a centralised database.

- Sample or dummy data will be used where real institutional data is not available.

## 9. Initial Constraints

- Real IQAC data may not be shared with us, so testing will mostly use sample data.

- Requirements may change once we show early versions to users.

- Uploaded documents and user data need to be protected properly.

- Limited chance to test with actual IQAC members, so feedback cycles may be slow.

- File storage limits mean upload size will have to be capped.

- The system depends on internet and server availability.

## 10. Initial Success Criteria

The project will be treated as successful if the team can demonstrate that:

- Different roles log in and see only the functions meant for them.

- An authorised user can create an activity, assign it and set a deadline.

- The assigned user can see the activity in their own list and update its status.

- An activity moves correctly through all its stages up to completed.

- Evidence files can be uploaded, stored and opened again later.

- Submitted evidence can be verified by IQAC administrator.

- The outcome of a completed activity can be recorded and retrieved.

- Overdue activities are clearly visible and reminders are sent.

- The dashboard correctly shows counts of pending, ongoing and completed activities.

- A report can be generated and exported for a chosen department or time period.

- Important functions have test cases and the results are recorded.

- Defects found during testing are logged and fixed.

## 11. Simple Working Flow

Create Activity → Assign Person/Department → Set Deadline and Quality Area → Update Progress → Upload Evidence → Verify Evidence → Record Outcome → Complete → Monitor and Generate Report

# Lab Assignment 2: Requirements Specification

## 11. User Classes

### 11.1 Student

Students take part in the feedback side and data collection side of IQAC work. They shall be able to:

- authenticate

- view feedback forms

- fill and submit feedback forms

- receive notifications about open forms and deadlines

- view their submission history.

### 11.2 Staff

Faculty and staff to whom activities are assigned. They should be able to:

- view the activities assigned to them

- update the status of activity

- upload evidence files for an activity

- add remarks on an activity

- receive deadline reminders

### 11.3 Department

The department coordinator manages the activities of their own department. They should be able to:

- create an activity

- assign an activity

- tag an activity to a domain area

- set and modify deadlines

- submit an activity for verification

- monitor department level progress

### 11.4 IQAC Member

The IQAC member reviews the work submitted by departments. The member shall be able to:

- review submitted activities and their evidence

- verify evidence

- return an activity for correction

- provide comments while returning

### 11.5 IQAC Coordinator

The IQAC coordinator plans and monitors the complete quality cycle. The coordinator shall be able to:

- define domain and activity categories

- plan activities for an academic year

- monitor progress

- view all dashboards and audit information.

### 11.6 Administrator

The administrator shall be able to:

- manage users

- assign roles

- monitor system activity

- access administrative reports and the activity log.

### 11.7 Institute Management

Management users should have access to appropriate aggregated reports and dashboards for monitoring the quality related work of the institute.

## 12. System Context

in the system context file

## 13. Functional Requirements

### 13.1 Authentication and Account Management

#### FR-001 - User Login

The system shall allow a registered user to authenticate using valid institutional credentials.

#### FR-002 - Authentication Failure

The system shall notify the user when authentication fails without unnecessarily revealing sensitive authentication information.

#### FR-003 - Logout

The system shall allow authenticated users to terminate their session.

#### FR-004 - Role Assignment

The system shall allow authorised administrators to assign roles to users.

#### FR-005 - Role-Based Access

The system shall restrict system functions according to the user’s assigned role.

### 13.2 Activity Creation and Management

#### FR-006 - Create Activity

The system shall allow an authorised coordinator to create an IQAC activity.

#### FR-007 - Activity Information

The system shall allow a coordinator to specify:

- title

- description

- domain or criterion tag

- activity category

- responsible person or department

- planned start date

- deadline

- expected outcome

- required evidence type

- priority

#### FR-008 - Save Activity Draft

The system shall allow a coordinator to save an incomplete activity as a draft.

#### FR-009 - Edit Activity

The system shall allow an authorised coordinator to modify an activity subject to its current status.

#### FR-010 - Assign Activity

The system shall allow a coordinator to assign an activity to a responsible person or department.

#### FR-011 - Reassign Activity

The system shall allow an authorised user to reassign an activity to another responsible user.

#### FR-012 - Set Deadline

The system shall allow an authorised user to set and modify the deadline of an activity.

#### FR-013 - Cancel Activity

The system shall allow an authorised user to cancel an activity with a recorded reason.

### 13.3 Activity Discovery and Tracking

#### FR-014 - Activity Listing

The system shall display activities to users according to their role and department.

#### FR-015 - My Activities

The system shall display to each responsible user the list of activities assigned to them.

#### FR-016 - Activity Search

The system shall allow users to search for activities.

#### FR-017 - Activity Filtering

The system shall allow users to filter activities by department, domain area, status, deadline and responsible user.

#### FR-018 - Activity Details

The system shall display complete relevant information for an activity.

#### FR-019 - Overdue Indication

The system shall clearly indicate activities whose deadline has passed and which are not yet completed.

### 13.4 Progress and Status Management

#### FR-020 - Update Status

The system shall allow the responsible user to update the status of an assigned activity.

#### FR-021 - Progress Remarks

The system shall allow the responsible user to add remarks.

#### FR-022 - Status Transition Control

The system shall allow only valid status transitions.

#### FR-023 - Record Outcome

The system shall allow the responsible user to record the outcome of an activity.

#### FR-024 - Submit for Verification

The system shall allow the responsible user to submit an activity for verification.

### 13.5 Evidence Management

#### FR-025 - Upload Evidence

The system shall allow an authorised user to upload evidence files against an activity.

#### FR-026 - Supported Formats

The system shall accept evidence files in common formats such as PDF, DOCX, JPG and PNG.

#### FR-027 - File Size Validation

The system shall reject evidence files that exceed the maximum size.

#### FR-028 - Evidence Association

Each evidence file shall be associated with the relevant activity and the uploading user.

#### FR-029 - View Evidence

The system shall allow authorised users to view the evidence.

#### FR-030 - Delete Evidence

The system shall allow an authorised user to remove a wrongly uploaded evidence file before verification.

### 13.6 Verification Management

#### FR-031 - Review Submission

The system shall allow an IQAC member to review a submitted activity along with its evidence.

#### FR-032 - Verify Activity

The system shall allow an IQAC member to mark an activity as verified.

#### FR-033 - Return Activity

The system shall allow an IQAC member to return an activity for correction.

#### FR-034 - Return Reason

The system shall allow an IQAC member to provide a reason or comment while returning an activity.

#### FR-035 - Verification History

The system shall maintain a record of verification decisions for each activity.

### 13.7 Feedback Management

#### FR-036 -Create Feedback Form

The system shall allow an authorised coordinator to create a feedback form linked to an activity.

#### FR-037 - Publish Feedback Form

The system shall publish a feedback form to the intended user group for a defined period.

#### FR-038 - Submit Feedback

The system shall allow an eligible user to submit a feedback response while the form is open.

#### FR-039 - Duplicate Prevention

The system shall prevent the same user from submitting the same feedback form more than once, unless multiple responses are permitted.

#### FR-040 - Feedback Summary

The system shall provide a summary of the collected feedback responses to authorised users.

### 13.8 Notification Management

#### FR-041 - Assignment Notification

The system shall notify a user when an activity is assigned to them.

#### FR-042 - Deadline Reminder

The system shall send a reminder to the responsible user before the deadline of an activity.

#### FR-043 - Overdue Notification

The system shall notify the responsible user and the coordinator when an activity becomes overdue.

#### FR-044 - Verification Notification

The system shall notify the responsible user when an activity is verified or returned.

#### FR-045 - Feedback Notification

The system shall notify eligible users when a feedback form is open for submission.

### 13.9 Reporting and Dashboard

#### FR-046 - Activity Report

The system shall generate activity reports for authorised users.

#### FR-047 - Department Report

The system shall generate department-wise reports for a chosen time period.

#### FR-048 - Domain-wise Report

The system shall generate reports grouped by domain area.

#### FR-049 - Report Export

The system shall allow authorised users to export generated reports in a common file format.

#### FR-050 - Dashboard

The system shall display counts of pending, ongoing, completed, overdue and verified activities to authorised users.

### 13.10 Audit and History

#### FR-051 - Activity History Log

The system shall maintain a history of significant changes made to an activity.

#### FR-052 - View History

The system shall allow authorised users to view the history log of an activity.

#### FR-053 - Administrative Audit

The system shall record significant administrative actions such as role changes and configuration changes.

## 14. Business Rules

```text

ID                                               Business Rule
BR-001                                           Only authorised users can create activities.
BR-002                                           Every activity must have one responsible
                                                 person or department.
BR-003                                           Every activity must have a deadline.
BR-004                                           An activity must be tagged to a domain area
                                                 before it is assigned.
BR-005                                           Only the assigned responsible user or an
                                                 authorised coordinator can update the
                                                 progress of an activity.
BR-006                                           A completed activity must be verified by an
                                                 IQAC member before it is counted in reports.
BR-007                                           Returned activities must be corrected and
                                                 resubmitted before verification.
BR-008                                           Evidence cannot be deleted after an activity
                                                 has been verified.
BR-009                                           An activity whose deadline has passed and
                                                 which is not completed is treated as overdue.
BR-010                                           Only authorised users can access
                                                 administrative and institute level reports.
BR-011                                           Feedback can be submitted only while the
                                                 form is open.
BR-012                                           Cancelled activities cannot be updated or
                                                 verified.
BR-013                                           Uploaded files must be within the configured
                                                 size and format limits.

```

## 15. Non-Functional Requirements

### 15.1 Performance

NFR-001: The system should provide acceptable response times for normal user operations.

NFR-002: Search and filtering of activities should return results within an acceptable time.

NFR-003: The system should support the number of concurrent users expected in an institute.

NFR-004: Evidence upload of a file within the allowed size limit should complete in an acceptable time.

### 15.2 Security

NFR-005: Protected functionality shall require authentication.

NFR-006: Access to functionality shall be controlled by user roles.

NFR-007: Uploaded evidence shall be accessible only to authorised users.

NFR-008: Sensitive information shall not be exposed to unauthorised users.

NFR-009: Administrative operations should be auditable.

### 15.3 Usability

NFR-010: The interface shall use consistent navigation.

NFR-011: Error messages shall be understandable to users.

NFR-012: Common activities such as updating status and uploading evidence should require minimal unnecessary interaction.

NFR-013: The pending and overdue work of a user should be visible on a single screen.

### 15.4 Reliability

NFR-014: Activity and evidence records shall be maintained reliably.

NFR-015: Uploaded evidence shall not be lost during normal system operation.

NFR-016: A failed upload shall not leave an incomplete evidence record.

### 15.5 Availability

NFR-017: The system should be available during normal working hours of the institute, except during planned maintenance.

### 15.6 Maintainability

NFR-018: The software shall follow a modular architecture.

NFR-019: Source code shall be maintained using version control.

NFR-020: Software documentation shall be maintained alongside relevant system changes.

### 15.7 Scalability

NFR-021: The architecture should allow the system to support increasing numbers of users, activities and evidence files.

### 15.8 Compatibility

NFR-022: The system should operate correctly on commonly used modern web browsers.

### 15.9 Privacy

NFR-023: Personal information and feedback responses shall be accessible only to authorised users.

### 15.10 Auditability

NFR-024: Significant administrative and verification actions should be recorded to support accountability and troubleshooting.

## 16. Data Requirements

The initial logical information requirements include the following entities.

User Possible attributes:

- User ID

- Name

- Email

- Contact information

- Department

- Role

- Account status

Department Possible attributes:

- Department ID

- Department name

- Head of department

- Contact information

Domain Area Possible attributes:

- Domain ID

- Domain name

- Description

Activity Possible attributes:

- Activity ID

- Title

- Description

- Domain ID

- Department ID

- Created by

- Assigned to

- Planned start date

- Deadline

- Priority

- Status

- Outcome

- Created on

- Last updated on

Evidence Possible attributes:

- Evidence ID

- Activity ID

- File name

- File type

- File size

- Uploaded by

- Upload date

- Verification status

Verification Possible attributes:

- Verification ID

- Activity ID

- Verified by

- Decision

- Comments

- Decision date

Feedback Form Possible attributes:

- Form ID

- Title

- Linked activity ID

- Target user group

- Open date

- Close date

- Status

Feedback Response Possible attributes:

- Response ID

- Form ID

- User ID

- Responses

- Submission date

Notification Possible attributes:

- Notification ID

- Recipient

- Notification type

- Message

- Timestamp

- Status

Activity Log Possible attributes:

- Log ID

- Activity ID

- User ID

- Action

- Old value

- New value

- Timestamp

## 17. Activity Lifecycle

The activity entity may pass through the following states:
Draft
↓
Created
↓
Assigned
↓
In Progress
↓
Evidence Uploaded
↓
Completed
↓
Submitted for Verification
↓

/ \

/ \
Verified     Returned
↓
In Progress (rework)
An activity may also move to the Cancelled state from any state before verification, and to the Overdue condition when its deadline passes before completion.

## 18. Major Use Cases

The initial use-case catalogue is as follows:

```text

ID                                 Use Case                       Primary Actor
UC-001                             Login                          All users
UC-002                             Manage Users                   Administrator
UC-003                             Manage Domain Areas            IQAC Coordinator
UC-004                             Create Activity                Department Coordinator
UC-005                             Assign Activity                Department Coordinator
UC-006                             View Assigned Activities       Faculty / Staff
UC-007                             Update Activity Status         Faculty / Staff
UC-008                             Upload Evidence                Faculty / Staff
UC-009                             Record Outcome                 Faculty / Staff
UC-010                             Submit for Verification        Faculty / Staff
UC-011                             Verify Evidence                IQAC Member
UC-012                             Return Activity                IQAC Member
UC-013                             Search and Filter Activities   All authorised users
UC-014                             Send Deadline Reminder         System
UC-015                             View Dashboard                 IQAC Member / Coordinator
UC-016                             Generate Report                Authorised User
UC-017                             Export Report                  Authorised User
UC-018                             Create Feedback Form           IQAC Coordinator
UC-019                             Submit Feedback                Student
UC-020                             View Activity History          Authorised User

```

## 19. Detailed Use Case Example

UC-008 -Upload Evidence

Primary Actor: Faculty / Staff (responsible user)

Preconditions:

- User is authenticated.

- Activity exists.

- Activity is assigned to the user.

- Activity is not yet verified.

Main Flow:

- User opens the activity from their assigned list.

- System displays activity details.

- User selects Upload Evidence.

- User chooses a file and enters a short description.

- System validates the file format.

- System validates the file size.

- System stores the file and links it to the activity and the user.

- System records the upload in the activity history log.

- System displays a confirmation.

- System updates the activity status to Evidence Uploaded.

Alternative Flows:

- If the file format is not supported → system rejects the upload and informs the user.

- If the file exceeds the size limit → system rejects the upload and informs the user.

- If the activity is already verified → system does not allow the upload.

- If the upload fails → system does not create an evidence record and informs the user.

Postcondition:

A valid evidence record exists against the activity and is visible to the coordinator and IQAC member.

## 20. User Stories

The requirements will also be represented in Agile form.

#### US-001

As a user, I want to log in so that I can securely access the IQAC Activity Tracking System.

#### US-002

As an administrator, I want to manage user roles so that access to the system is controlled.

#### US-003

As a department coordinator, I want to create an activity so that the quality work is recorded in one place.

#### US-004

As a department coordinator, I want to assign an activity to a person so that ownership is clear.

#### US-005

As a department coordinator, I want to set a deadline so that the work is completed on time.

#### US-006

As a faculty member, I want to see the activities assigned to me.

#### US-007

As a faculty member, I want to update the status of my activity so that progress is visible to others.

#### US-008

As a faculty member, I want to upload evidence against an activity so that the proof stays with the activity itself.

#### US-009

As a faculty member, I want to record the outcome of a completed activity so that its result is documented.

#### US-010

As an IQAC member, I want to verify submitted evidence so that only genuine work is counted.

#### US-011

As an IQAC member, I want to return an activity with a reason so that the mistake can be corrected.

#### US-012

As a user, I want to receive reminders before a deadline so that I do not miss it.

#### US-013

As an IQAC coordinator, I want to see a dashboard so that I know the overall status at a glance.

#### US-014

As an IQAC coordinator, I want to generate and export domain-wise reports.

#### US-015

As a student, I want to fill a feedback form so that my opinion is recorded.

#### US-016

As an authorised user, I want to view the history of an activity so that I can see who changed what and when.

## 21. Acceptance Criteria Example

US-008 -Upload Evidence

```text

ID                                               Acceptance Criterion
AC-01                                            User must be authenticated
AC-02                                            Activity must exist and be assigned to the user
AC-03                                            Activity must not already be verified
AC-04                                            File format must be one of the supported
                                                 formats
AC-05                                            File size must be within the configured limit
AC-06                                            Successful upload must create an evidence
                                                 record linked to the activity
AC-07                                            The uploaded file must be openable again
                                                 later
AC-08                                            The upload must be recorded in the activity
                                                 history log
AC-09                                            User must receive a confirmation

```

## 22. Requirements Prioritization

**Must Have**

- Authentication

- Role-based access

- Activity creation

- Activity assignment

- Deadline setting

- Status update

- Evidence upload and storage

- Evidence verification

- Outcome recording

- Search and filtering

**Should Have**

- Deadline reminders and overdue notifications

- Dashboard

- Reports with export

- Activity history log

- Domain area tagging and grouping

- Feedback forms

**Could Have**

- Advanced analytics

- Configurable report templates

- Comment threads on an activity

- Calendar view of deadlines

**Won't Have in Initial Release**

- Full ERP functionality

- Payment handling

- Online examination and attendance modules

- Automatic generation of the complete AQAR in NAAC format

- Direct integration with NAAC or university portals

- Mobile application

- AI-based suggestions or predictions

## 23. Requirements Traceability

Requirements Traceability Matrix (RTM).

An initial version:

```text

Requirement           User Story                  Use Case           Test Case
FR-006                US-003                      UC-004             TBD
FR-010                US-004                      UC-005             TBD
FR-015                US-006                      UC-006             TBD
FR-020                US-007                      UC-007             TBD
FR-025                US-008                      UC-008             TBD
FR-023                US-009                      UC-009             TBD
FR-032                US-010                      UC-011             TBD
FR-033                US-011                      UC-012             TBD
FR-042                US-012                      UC-014             TBD
FR-050                US-013                      UC-015             TBD
FR-049                US-014                      UC-017             TBD
FR-038                US-015                      UC-019             TBD
FR-052                US-016                      UC-020             TBD
Note: The TBD entries will be filled later in the testing phase.

```

## 24. Requirements Validation

**Correctness**

The requirements represent the main needs of the identified stakeholders, including students, faculty/staff, department coordinators, IQAC members, IQAC coordinators and administrators.

**Unambiguity**

Requirements have been written using clear and specific statements beginning with “The system shall”.

**Completeness**

The SRS covers authentication, role-based access, activity creation and assignment, status tracking, evidence management, verification, feedback, notifications, reporting, dashboards and audit history.

**Consistency**

The functional requirements, business rules, use cases, user stories and acceptance criteria were reviewed to ensure that they do not contradict one another.

**Verifiability**

The requirements are stated in a manner that allows them to be tested.

**Feasibility**

The requirements are considered technically feasible for implementation by a student team within one semester.

**Traceability**

Test cases are currently marked as TBD and will be added during the testing phase.

**Prioritization**

Requirements have been classified into Must Have, Should Have, Could Have and Won't Have in the initial release.

**Modifiability**

Requirements are organised into separate functional areas such as authentication, activity management, evidence management, verification, feedback and reporting.

## 25. Example of Requirement Quality

**Poor**

The system should handle evidence properly and be easy to use.

This is ambiguous and difficult to verify.

**Better**

The system shall allow an authorised user to upload evidence files in PDF, DOCX, JPG or PNG format up to the configured maximum size, and shall link each uploaded file to the relevant activity and the uploading user.

and

The system should provide acceptable response times for normal user operations under expected workload.

## 26. Requirement Change Management

Because the IQAC Activity Tracking System uses Agile development, requirements can change once early versions are shown to IQAC members.

For example:

Change Request: Allow an activity to have more than one responsible user.

The team should follow:

Change Request → Impact Analysis → Requirement Update → Backlog Update → Prioritization → Sprint Planning → Design Change → Implementation → Testing → Release

The change should also update relevant documentation and traceability.

## 27. Future Requirements

Potential future requirements include:

- automatic generation of the AQAR document in the required format

- integration with institutional authentication (single sign-on)

- integration with the institutional ERP

- mobile application for status updates and evidence upload

- bulk import of past activities and evidence

- advanced analytics and trend comparison across cycles

- automatic reminders through email and messaging services

- version control of evidence documents

- digital signature on verified activities

- multi-year cycle comparison dashboards.

## 28. SRS Baseline and Versioning

- Initial baseline: SRS v1.0

- Version Control Information: SRS v1.0 covers authentication and role-based access, activity creation, assignment, deadline and status tracking, evidence upload and verification, notifications, feedback forms, dashboards and exportable reports. Feedback forms and reporting are included at a basic level only.

## AI Usage Policy – Student Declaration

AI tools may be used as supporting tools for this assignment. The team is responsible for the correctness, consistency and understanding of all submitted requirements.

- We have disclosed the use of AI tools, if any.

- AI-generated suggestions have been reviewed, verified and adapted by the team.

- We understand and can explain the submitted requirements, use cases and user stories.

- We have verified that the requirements are consistent with our project's scope.

- The final SRS represents our team's understanding and decisions.

| Field | As submitted |
| --- | --- |
| AI Tool(s) Used | Chat GPT |
| Purpose of AI Use | markdown making |
| Team ID | T096 |
| Team Representative | Manas Gupta |
| Date | 7 September 2026 |

## Team Contributions

| Team member | Roll number | Contribution recorded in source |
| --- | --- | --- |
| Shivam Sharma | 24UCS269 | Brain Storming |
| Garv Jain | 24UCS270 | Document Making |
| Dipanshu Soni | 24UCS271 | Brain Storming |
| Manas Gupta | 24UCS272 | Document Making |
