# Alma Take-Home Assignment
Source: https://you.ashbyhq.com/tryalma/assignment/baf857fc-b4eb-4f36-ba35-362e0d89909b
Fetched: 2026-09-06

## Functional Requirements
Develop an application to support creating, getting and updating leads. A lead is a form PUBLICLY available for prospects to fill in, the required fields include, first name, last name, email, resume / CV. Once the lead is submitted by a prospect, the application will send emails to both the prospect and an attorney inside the company. In addition, the application powers an internal UI guarded by auth to render a list of leads with all the information filled in by the prospect. Each lead also has a state, it starts with a PENDING state and transitions to REACHED_OUT when marked manually by an attorney after he / she reaches out to the prospect.

## Tech Requirements
Create a system design to fulfill the above requirements. Develop the web app & APIs E2E using coding agents of your choice. The APIs need to be implemented using FastAPI and the web app using NextJS. Add a storage to persist data and integrate with an email service. Properly structure the code similar to how you would for a production level repo.

## Submission Guidance
- Submit your code to a publicly available github repo.
- Submit a document on how to run your application locally in the same repo.
- Submit a design document on why/how you make those design choices in the same repo.
- Submit a document on your coding-agent usage. Heavy use is encouraged — they're evaluating how you use agents, not whether.
  - A short writeup (1/2 page max): which tools you used, what you delegated vs. wrote yourself and why, and one place the agent produced wrong or subtly bad code — how you caught it and fixed it.
  - Representative prompt logs or session transcripts (excerpts are fine).
  - Attribution in your commits or a NOTES file marking agent-generated vs. hand-written code.

## Deadline
Upload the github link in the assignment document within 6 hours since you start the exercise. Upload a short screen recording (e.g., Loom) showing the E2E workflow.

## Submission
Ashby page has a file upload + notes field and a "Submit Assignment" button.
