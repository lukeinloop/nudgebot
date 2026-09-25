# Nudgebot
**Nudgebot** is a Discord bot designed to help students stay organized and keep track of their coursework. The bot connects a class Discord server with Canvas to provide students with assignment information, reminders, and other useful course updates directly through Discord.

The goal of the bot is to make it easier for students to manage assignments and communicate with classmates without constantly switching between Discord and Canvas. 

> **!!WARNING!!** Academic Proof of Concept
>
> NudgeBot is a semester long class project and proof of concept. It is not intended for production use and **should not** be used with real or sensitive Canvas credentials.
>
> The current implementation **does not securely store Canvas API keys**. The bot is only run when needed for development and demonstrations.
>
> These limitations are intentional for the scope of the current project. A production implementation would require more work around credential security, authentication, database management, and other security concerns.

## Project Status

NudgeBot is currently an **academic proof of concept** under active development as part of OU's Software Engineering course.

This project is currently focused on implementing and demonstrating core Discord and Canvas integration. Features and implementation details may change throughout the semester as development continues.

NudgeBot is **not currently intended for production use** and should not be used with real or sensitive Canvas or Discord credentials.

## Features 

### Currently Implemented
 * Discord slash commands
 * Canvas account linking
 * Canvas API integration
 * Retrieval of Canvas courses
 * SQLite database for user and Canvas info
### Planned
 * Group project progress tracking
 * Assignment due date reminders
 * Professor tools
 * Settings customization
 * Additional Canvas course information

## Installation
### For Users
The current version of NudgeBot is a proof of concept project and is not intended for use by the general public.  
  
A public bot invite link will not be provided while the project is in its current proof of concept state.

### For Developers
#### Requirements
- Python 3.x
- A Discord application and bot
- A dDiscord development server
- A Canvas account with permissions to generate API keys
- Git

#### Installing Dependencies 
Clone the repository and install the required Python libraries: 
```
pip install -r requirements.txt
```
The project currently uses the following libraries:
- aiosqlite
- discord.py
- httpx
- python-dotenv

#### Environment Variables
Create a copy of the `.env-example` file and rename it to `.env`. 

The .env file should contain the configuration required to run the bot:  
```
TOKEN=discord_bot_token  
GUILD_ID=discord_server_id  
```

Copy the token from the Discord Developer Portal > Applications > NudgeBot > Bot and paste it in for the `TOKEN` environment variable.

Do not commit .env or any other file containing sensitive credentials to the repository.

#### Running the Bot
Once the dependencies and environment variables have been configured run:    
```
python main.py
```   
The application will initialize the database before starting the bot.

## Usage
NudgeBot currently supports the following slash commands.
  
### `/link`  
  
- Begins the Canvas account linking process.

- The bot sends instructions to the user through a direct message on Discord. The user can then provide their Canvas API token through the DM.

**WARNING:** Canvas API tokens are **not** currently stored securely. Do **not** use a sensitive Canvas account with this proof of concept implementation. 
  
### `/courses`  
  
- Retrieves the active courses associated with the linked Canvas account.  
  
- The bot displays the course names along with the course ID in an ephemeral message, which means the message is only visible to the user who invoked the command. 
  
Additional commands will be documented here as they are implemented.

## Development
NudgeBot is collaboratively developed as part of a semester long university course. 
  
All branches should correspond to a sprint backlog item.

### Feature Branches
For new features, create a new feature branch using:  
`feat/<feature-name-or-backlog-ID>`

For example:  
`feat/assignment_reminders`    
`feat/courses`

### Bug Fixes
Bugs should receive their own branch using
`bug/<bug-name-or-backlog-ID>`

For example:  
`bug/discord_token_storage`  
`bug/assignment_reminder_delay`

### Pull Requests
Once a feature or bug fix is complete:
1. Push the branch to the repository 
2. Open a pull request targeting main
3. Ensure the changes are formatted and tested
4. Request a code review
5. Merge the pull request once the review process has been completed

### Code Formatting 
This project uses the [Black Python formatter](https://pypi.org/project/black/).
  
Before submitting a pull request, format the project with:  
  
`black .`

Contributions should be formatted with Black before being merged into the main branch.

## Security
NudgeBot is currently not suitable for handling real user credentials or sensitive information. 
  
Known limitations include:  
- Canvas API tokens are not stored using production grade encryption.
- Application has not undergone a formal security audit
- The current database deployment is meant for development rather than production deployment
  
These limitations are part of the current proof of concept implementation.  
  
A production implementation would require at least:
- A more secure credential management strategy
- Appropriate authentication
- Peristent and properly secured database infrastructure
- Backups
- Migrations
- Access controls
- Monitoring 
- Security testing

## Authors and acknowledgment
Originally written for the CS-3203 Software Engineering class at the University of Oklahoma in Fall 2026.
Group K: Luke Sewell, Janes Le, Daniel Brown.

## License
Copyright 2026 Luke Sewell, Janes Le, Daniel Brown.

This repository is publicly available for course related review and collaboration. No open source license is currently granted.

Unless a license is added to this repository, the source code should not be assumed to be available for reuse, modification, or redistribution.  
  
If the project team and course instructor decide to release the project under an open source license later on, the appropriate license will be added here.