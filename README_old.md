<img width="6057" height="1817" alt="Flow" src="https://github.com/user-attachments/assets/669bfe68-0352-4e77-84f7-2994a54a599f" /># Project Management - 5 Week Plan and Task Delegation 
While overloading documentation is a negative in general, not enough documentation is just as bad. You will have 5 weeks from now to do the project which means, you need to create a timeline of what needs done, and who's going to do it. Make a quick list of tasks that need done, identify who is going to do them, and submit it. (Read the post from the project management institute about agile documentation (https://www.pmi.org/disciplined-agile/agile/documentation).)

# Task Area Delegation
 * Audio/Speech-To-Text - Sparkes
 * Database - how to store records - Matthew
 * LLM Model - how to summarize - James
 * GUI design - how to retrieve records - Hailey
 * Float/glue - help where needed, keep group together and on task - Minh

# Task List
 * One NFR (nonfunctional requirement) per group member
 * 

# 5 Week Plan
Minimum viable product:
 * Program to convert mp4 raw audio -> transcription -> translation -> store data record -> summarizer -> output summary & transcript + gui record retrieval system
 * => Sparkes' domain (audio/speech-to-text):
 *     Input: raw mp4 audio file of a patient/therapist session, possibly in non-English
 *     Processes: language detection, speaker identification (diarization), audio transcription (speech-to-text), text translation to US English
 *     Output: raw text output file of speaker-identified, English text transcription of session
 * => James' domain (summarize the transcript):
 *     Input: raw text output file of speaker-identified, English text transcription of session
 *     Processes: data cleaning/processing (strip unneccessary whitespace, possibly speaker labels, etc), summarize transcript into summary text
 *     Output: raw text summary of transcript
 * => Matthew's domain (database/storing the data):
 *     Input: raw text transcript, raw text summary of transcript, metadata
 *     Processes: data cleaning/standardizing?, local vector storage
 *     Output: N/A - record is stored for later retrieval in raw text format
 * => Hailey's domain (GUI/front end/data retrieval):
 *     Input: existing datastore of record information, user interaction to choose action:
 *       create new patient (create)
 *       view patient record (read)
 *       add session transcript to existing patient (update)
 *       edit patient metadata (update)
 *       delete patient (delete)
 *       delete patient session (delete)
 *     Processes: GUI design (CRUD system more or less), detailed list display, pagination?, search/sort/filter results?
 *     Output: Display the patient's record data on the screen
 * => unassigned goals
 *   how to identify/gather metadata (therapist, client ID, datetime, location/provider, etc) and how/where to display metadata
 * => Minh's domain (float):
 *   Documentation? User Manual? User Experience? Quality Control/Assurance?

## Week 1 (1/21/2026 - 1/27/2026):  
 * Full tech stack setup on all group members machine
 * Tech stack setup in terms of what tool is where in the workflow
 * SQLite? - may not be suitable
 * Python
 * Research: DB solutions for storing vector information
 * Design sketches - program flow chart, general design structure

## Week 2 (1/28/2026 - 2/3/2026):  
 * Basic audio ingestion pipeline
 * Speech-to-text prototype
 * GUI skeleton:

## Week 3 (2/4/2026 - 2/10/2026):  
 * Implement summarization pipeline
 * Clean and normalize transcript text
 * Generate summary output
 * Store transcripts and summaries
 * Implement CRUD operations

## Week 4 (2/11/2026 - 2/17/2026): 
 * QA Testing
 * Edge case testing

## Week 5 (2/18/2026 - 2/24/2026):  
 * Functional Prototype working
 * Cleanup
 * Bug Fixes



# SRS Document (In Class Group Work) 
You are going to need an SRS document for this project, but it's going to be minimal.  I don't want the complete thing because that's just an overload of tasks. Instead, what I want is section 1 (make sure to **document your assumptions**!) and then, each person in the group is going to focus on ONE quality attribute (non-functional requirement) and contribute it based on the notes from class.

This assignment is just the participation grade for the in class portion and all you need to submit is a statement of what part of section 1 you wrote and what quality attribute you are working on.


# Introduction

## Purpose
The purpose of this Software Requirements Specification (SRS) is to define the requirements for a local, desktop-based transcription and assessment summarization tool designed for psychologists. The system aims to modernize the current workflow of handwritten notes by automating the transcription of client sessions and generating behavioral summaries. The system is intended for use in the juvenile mental health system and is designed to assist providers in maintaining consistent records over long-term patient care. It is also intended to support situations where records may need to be reviewed by substitute providers. This tool is specifically designed to function within high-security environments (e.g., prisons, facilities for at-risk youth) where data privacy regulations strictly prohibit cloud-based storage or external data transmission.

## Scope
The software will be a standalone desktop application capable of ingesting audio recordings (specifically MP4 format) from external recording devices. The system will perform the following core activities:

* __Local Processing__: Perform offline speech-to-text transcription and natural language summarization without internet connectivity.
* __Multilingual Support__: Transcribe English and Spanish audio inputs, ensuring all output documentation (transcripts and summaries) is generated in English.
* __Patient Management__: Allow psychologists to associate recordings with specific client profiles to track historical trends, behavioral themes, and treatment continuity.
* __Administrative Auditing__: Provide local querying capabilities for administrators to audit records and locate notes.

__Out of Scope__:
* Cloud storage or synchronization features.
* Generation of official treatment plans (slated for future "stretch" development).
* Mobile application interfaces.

## Product Overview

### Product Perspective
This system is a self-contained software product that operates independently on the user's local machine. It replaces a manual workflow involving handwritten notes and unorganized audio files.

The system operates entirely offline and does not depend on cloud services, external APIs, or internet connectivity. All data processing and storage occur locally within the workstation.

The application integrates with external audio recording devices that generate MP4 files. These devices are not controlled by the system; audio files are transferred manually via secure physical media such as USB drives.

Internally, the system is composed of the following major components:

* Audio ingestion and preprocessing module
* Speech-to-text transcription module
* Local summarization module
* Local encrypted data storage
* Graphical user interface

The operational environment includes macOS, Windows, and Linux platforms. No system data may leave the host machine at any time.
- See Flowchart

### Product Functions
The major functions of the system include:

1. Secure ingestion of MP4 audio recordings from external devices.
2. Automatic language detection for supported languages.
3. Offline speech-to-text transcription.
4. Cleaning and normalization of transcript data.
5. Automated summarization of session transcripts.
6. Creation and management of patient profiles.
7. Association of multiple sessions with a single patient record.
8. Local storage of transcripts, summaries, and metadata.
9. Search, filter, and retrieval of patient records.
10. Administrative auditing with restricted modification access.
11. Status reporting and progress feedback during processing.

### User Characteristics
* Primary User (Psychologist): Non-technical subject matter experts. They require an intuitive interface that minimizes technical friction, allowing them to focus on patient analysis rather than software configuration. They often work with translators.

* Secondary User (Administrator): Responsible for compliance and auditing. They require tools to search and verify records without necessarily altering patient data.

### Limitations
* Performance & Hardware constraints:
  * The system is limited by the storage capacity and processing power of the host laptop, as offloading processing to the cloud is prohibited.
  * The system's performance will be constrained by the hardware running it, namely CPU and presence of a dedicated Nvidia GPU.
  * The processing time need not be real-time, but a 1:1 (or better) input audio duration:processing duration would be ideal.
* Data Sovereignty:
  * No data may leave the local machine; all backups and history must be managed locally.
  * The system must be installed via an external drive (USB drive, etc) and no data may leave the local machine.
  * The local machine will not have internet access.
* Audio Quality:
  * The accuracy of the model is dependent on the quality of the input recording, which may vary in high-stress environments.
* Localization:
  * The system will be designed to digest multilingual audio files in mp4 format.
  * The graphical user interface will be designed in US English.
  * The system documentation will be in US English.
  * All data to be stored in the system will be standardized to US English.
* Usability:
  * The system will be able to be installed by a non-administrator user account.
  * The system should not require any additional installations such as runtime or third party external libraries to be installed.


## Definitions
* Local Processing: The execution of software commands and data storage strictly on the computer's hard drive, without utilization of remote servers or cloud computing.
* Transliteration vs. Translation: In this context, the system must translate Spanish audio directly into English text transcripts.
* Stretch Goal: A requirement (e.g., automated paperwork filling) desirable for future releases but not critical for the Minimum Viable Product (MVP).
* CPU vs GPU processing: Central Processing Unit (CPU) processing is achievable on all user devices, but the ideal is utilizing a dedicated Graphics Processing Unit (GPU) from Nvidia. A GPU will increase performance significantly.


## Non Functional Requirements
* Access Security: Not being able to connect to the internet for security reasons. -Minh
* Usability: Our application should be intuitive and easy to use. -Matthew
  * ### NFR-002: Usability
    * The user interface shall follow a clear clinical workflow from audio ingestion through summary review.
    * The system shall not require technical configuration by the end user.
    * All primary tasks shall be accessible within three or fewer user interactions from the main screen.
    * The system shall provide visible progress indicators during transcription and summarization.
    * The system shall clearly communicate its current state (idle, processing, completed, or error).
    * Error messages shall be human-readable and provide corrective guidance when possible.
    * The system shall not require command-line interaction or external documentation for normal operation.
* Efficiency: How quickly should we be able to create a transcription and notes? - James
* Installability: How should this be put on their machines and ran? - Sparkes
  * **NFR-001**: System Installability 
    * The system shall be installable by a **layman user** or **technician** in no more than 15 minutes.
    * The system shall **train/guide** the user through basic functionality requiring no more than 15 minutes.
    * The system should indicate its **state** to the user in a **clear** and **concise** way at all times.
    * The system should be able to gracefully **handle** common **errors,** and output **human-readable error messages** if unable.
    * The system should be easily installable.
    * The system should **leave no traces** (except for the data store, as per user choice) on the local device after uninstallation.
    * The system will be designed as a **fully featured single deployable version**, with **no planned updates** or maintainence schedule planned. 
* Confidentiality: Using HIPAA protected data and making sure things are secure. - Hailey


# Agile Documentation Strategies (from https://www.pmi.org/disciplined-agile/agile/documentation)

An important part of our solution is deliverable documentation, the kind of documentation needed by our stakeholders to work with, operate, and sustain the solution. This may include system overview documentation, user guides/help, training manuals, and operations guidelines, etc. There are several agile documentation strategies to keep in mind:
 * Invest in **quality** over documentation. The better designed our solution is, the easier it will be for stakeholders to understand it, and therefore generally less documentation will be required.
 * Write documentation that is **just barely good enough** (JBGE). When we do create documentation it should be JBGE﻿, or just barely sufficient, to fulfill the needs of our stakeholders and no more. Any investment in an artifact to make it more than good enough is a waste, and sufficiency is determined by the customer of the document, not the producer. Keep your documentation **concise**.
 * Document **stable concepts**, not speculative ideas. Speculative ideas, such as **requirements**, are likely to evolve over time. This in turn requires you to update your documentation. Whenever possible, wait until the material that you are describing is stable before you capture it in documentation.
 * Find better ways to **communicate**. If the purpose of a document is to communicate information to others, it is important to recognize that detailed documentation is one of the least effective means to accomplish that purpose. You have other communication options available to you to choose from.
 * Recognize that you need **some documentation**. A common, and unfortunately enduring, misunderstanding about agile is that agile teams don’t write documentation. Nothing could be further from the truth, and there is a wealth of information about agile/lean documentation strategies﻿ available to you that are leveraged within the Disciplined Agile (DA) tool kit.
 * **Work** closely **with** stakeholders. The only way we can write effective documentation is if we know **what** our stakeholders need and **how** they will work with the documentation that we produce. Effective documents tend to be single purpose and targeted at a specific audience. Figure 1 summarizes the **CRUFT** formula for calculating the effectiveness of a document as a percentage, and please note that 4 of the 5 factors rely on the customer of the document.
 * Effectiveness of a document = **C*R*U*F*T**
Where:
**C** = The percentage of content that is **correct**
**R** = The chance the document will be **read**
**U** = The chance that the content will be **understood**
**F** = The chance that the advice will be **followed**
**T** = The chance that the advice will be **trusted**
