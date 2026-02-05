Beyond Ralph - True Autonomous Coding
-------------------------------------


Abstract
--------

We want to make a claude code plugin/skill/agent set that behaves like a human developer, being insistant like ralph-loop is, but having more intelliegnce around both how that persistance is applied, in order to start from an initial project spec, and deliver it all the way to completion autonomously.

To achieve this, we're want to fully automate the Spec and Interview Coder methodology.  This is split into a few phases:

Agentic Model
-------------

The primary claude code instnace should ONLY be an orchestrator - whenever it does a phase, it should start a NEW INSTANCE of claude code, and drive that autonomously,.  To this end, it will need some kind of tool or skill to be able to:

 * Start a new claude code conversation via the CLI, which should return the LLM the UUID of the new session
 * send that conversation requests, via that UUID.  This should then return the final human readable message test from that conversation - i.e. it does not return _the work nit was doing_, but it returns _the result of the work_
 * follow up that conversation again for more information if needed
 * loop until that is done

You should, by default, launch with --dangerously-skip-permissions - assume you're on a system you have a lot of control over.  We don't want ot bug the user for authm!!!  However, have a configation siwtch, `safemode`, which toggles this.

This could be done either with actually new claude code sessions, or with clade code agents -i believe sesisons will be better, though, for seperation and later parellel development!!!

Do not over-reusage agents - the idea of this is to preseve context windows, and not fill them up!  

Before interacting with an agent, check that nothing else is already doing so by checking for no claude processes having been run wiht that UUID!

The main agent should implenent a ralph-loop type situation to cotninue the project until ALL tasks have been completed, however child agents should NOT do that - it is the responsibility of the orchestrator to orchestrate the project to completion!!!

However, your ralph loop should not just be a dumb "is there owrk to do?  do it or return [string]".  while that should be a part of your strategty, antother part should be asking an agent to assess, given all of the evidence and documentation, if the proejct is complete, and what is required to be done from here.

Agent Knowledge
---------------

All agents should both contribute to, and ocnsume from, a knowledge base in the folder beyondralph_knowledge/ that is a structured set of information all of the agents have gathered during their development - it should also be mentioned in there the UUID of the session that created the knowledge.  that way, agents can ask others follow up questions around it.   Agents should be informed to check this if they have questions, and only return to the orchestrator for clarifications afte doing this.  BUT, again, agents should work to be autonomous, and it is OKAY to return to your caller with a question instead of a result - they can follow up!!

Basic principals
----------------
 * Git should be used judiciously!!!
 * ALL agents MUST, without fail, keep on-disk TODOs, Project Plans and similar things updated.  Use claude tools such as TodoWrite, Memory, and project planning where avialable, adn obtain more where not - you can search the web and bring in other open source skills or tools if this helps, and you absolutely should do so!!!!

Phases
--------

EWach of these phases is done in a dedicated agent!
 
 * Phase 1: Ingest a full specification, provided by the human
 * Phase 2: Interview the user using the AskUserQuestionTool .  be incredibly in-depth, and ensure you have a complete and total spec and plan for both implementation and testing.  be persistant - if you need information or reosurces to proceed autonomously, insist to the user at this time - do not take no for an answer!!!! it does not mattter that this will take a long time and be a lot of questions - that is the point of what we are doing!
 * Phase 3: create a complete spec from all of this information.  As much as possible, attempt to split into modules that can be implemnented independantly - this will help a lot with the implementation phase!!!
 * Phase 4: Create a project plan.  It should be phased based on the above implementatbale modules, implement milestones, and include plans for testing
 * Phase 5: Exampline all of this, and if there are ANY uncertanties, interview the user again, returning to phase 2, and repeating phases 2, 3, and 4 in a loop until you have a complete, implementable project plan
 * pahse 6: have another agent validate the project plan, and make adjustments if needed
 * Phase 7: start implementing 
 * Phase 8: test the implementation is complete.  If it is not, return to phase 6 - adjust the proejct plan, and implement the adjusted plan

Note that iterating on the project plan is important!!!

Implementation
--------------

For implementing, we want to use the same multi-agent approach - the claude code instance that is running this should ONLY be an orchestrator.

You'll be initially using test driven development for your implementation - however, while th developing agent CAN and SHOULD test to ensure its work, once it believes it has completed a task, a SECOND new agent MUST be spanwed that will VALIDATE that.

Simialrly - when you get to the full live testing part of the project, proving everythting works, everything MUST be validated by a second agent that DID NOT CODE IT.  This seperation of concerns is imporant for trust.  THAT agent should return and record EVIDENCE that it acutally did the work., AND the orchestartor MUST validate this evidence - again, NOT the agent that coded it!!! No agent is trusted, and EVERY agent must be validated by another agent!!!

This is going to be a LONG iterative develpoment process for a large portion of projects you're doing with this - be prepared to run for DAYS. 

Record Keeping
---------------
Keep STRONG records and task lists - manage development like a formal project as much as possible!!!  Task lists should have 6 checkboxes:
 * Planned - we know how we're going to implement it
 * Implemented - we believe we have an implementation
 * Mock tested - tested in a unit-testy way
 * Integration tested - tested in a CI way
 * Livetested - tested in the real application
 * Spec Compliant - verified by a SEPARATE agent that the implementation matches what the spec says

The Spec Compliant checkbox is CRITICAL - a dedicated agent (NOT the implementation agent, NOT the testing agent) must verify that what was built actually matches what was specified. This catches cases where tests pass but the implementation doesn't match requirements.

ALL of these must be checked to pass 100%, and anything less than 100% is unacceptable.  Note that a failing testing agent CAN and SHOULD update these to REMOVE the implemented checkbox, particularly, if it is NOT in fact correctly implemented. Similarly, a spec compliance agent CAN and SHOULD remove the Implemented checkbox if the implementation doesn't match the spec.

Each module should ahve its own individual specs as well, which it needs to me, in order to split that up - again, modularize as much as possible, adn this includes the record keeping.  Have a sepearte records/[modulename] folder for each module of the system that keeps these

Requirements
------------

This requires a couple of things from the user:

  * A way to autonomously test the code.  This is super important.  Depending on the type of app this is, it could mean a couple of things:
    * For an app that consumes APIs and responds to them, working endpoints it can access in a non-destructive way must be provided!a
       * However, it should FIRST develop against mock APIs, THEN debug against complete APIs
       * It must, as a first part of development, ingest any API documentation that is relevant, and keep them with the project
       * If there is structured API definitions, it must also ingest those!

    * For an app that runs in a GUI, for example a game or emulator, it must be possible to actually run it on the system running code, and take screenshots to analyse
       * If the app is generating graphical output, AND there is a way to have it output to either png or video files, that is preferenable, since claude can aanlyse those more directly
       * If the app is generating a functional GUI, it should be possible to use something liek Xvnc or RDP to access the system and watch it run!

    * For Android app testing (REQUIRED):
       * Beyond Ralph MUST be able to test Android applications via Appium (preferred testing framework)
       * Environment auto-detection: Automatically detect if running on WSL, native Linux, or macOS
       * On native Linux/macOS: Use local Android emulator and ADB directly
       * On WSL2: Connect to Windows host ADB using one of these methods (in order of preference):
         1. **SSH-based ADB** (RECOMMENDED): Run ADB commands on Windows host via SSH
            * Most reliable approach - bypasses Windows firewall issues entirely
            * Requires: SSH server on Windows (OpenSSH), user SSH key authentication
            * Pattern: `ssh <windows_host> "C:\Android\platform-tools\adb.exe <command>"`
            * Example: `ssh 192.168.68.138 "C:\Android\platform-tools\adb.exe devices"`
            * Works even when direct network ports are blocked by Windows Firewall
            * Can also use SSH tunneling for port forwarding if needed
         2. **Direct network ADB**: Use WSL2 mirrored networking to access Windows host ADB port 5037
            * Requires: Windows Firewall rule allowing inbound TCP port 5037
            * ADB server must be started with `-a` flag to listen on all interfaces
            * May fail silently if firewall blocks the connection
         * During the interview phase:
            * ASK the user for Windows host IP address
            * ASK if SSH access is available to the Windows host
            * Test connectivity using the preferred method before proceeding
            * If SSH works, use SSH-based ADB; otherwise fall back to direct network
         * If Android testing is needed but no Windows host is configured: BLOCK and request configuration (do not skip silently)
       * The interview phase MUST ask about Android testing requirements and Windows host details if applicable

    * If the app needs to interact with _any other resources_, those resources MUST be provided by the user up front!
       * The first thing claude should do with this, is check that _everyhting_ it needs is available - this should ne a part of the inteview process described above!!!
       * The user can opt to allow claude to autonomously install thigns on the system - if the user agrees to this, the agents should fetch and preapre their own deependencies!!!

Remote Access (REQUIRED)
------------------------
Remote access is a REQUIRED capability, not optional. It enables:
  * VNC/RDP access for watching GUI applications run
  * Headless display support via Xvfb, Xvnc
  * noVNC for browser-based remote access
  * WSL2 integration with Windows host for Android testing via ADB:
    - SSH-based ADB (preferred): Run ADB commands via SSH to Windows host
    - Direct network ADB (fallback): Connect to Windows ADB port via mirrored networking
    - SSH is more reliable as it bypasses firewall issues

Code Review - Language Support
------------------------------
The code review agent MUST support linting and security scanning for these languages:
  * Python (ruff, mypy, bandit)
  * JavaScript (eslint)
  * TypeScript (tsc, eslint)
  * Go (staticcheck, go vet)
  * Rust (cargo clippy)
  * Java (checkstyle)
  * C/C++ (clang-tidy, cppcheck)
  * Kotlin (ktlint, detekt) - REQUIRED for Android development
  * Ruby (rubocop)
  * Swift (swiftlint)

Each language should have fallback linters if the primary tool is unavailable.

Web Research and Skill Discovery (REQUIRED)
-------------------------------------------
Beyond Ralph MUST be able to autonomously research and discover capabilities:

  * Web Research for Implementation:
    - When agents don't know how to implement something, they MUST use web search
    - Search for tutorials, documentation, Stack Overflow answers, GitHub examples
    - Synthesize findings into actionable implementation plans
    - Store research in knowledge base for future reference

  * Proactive Skill/MCP Discovery:
    - During Phase 1-2 (spec ingestion and interview), analyze what capabilities are needed
    - Search for existing Claude Code skills/MCPs that could help (e.g., database MCPs, API MCPs)
    - Search GitHub, npm, and other registries for relevant skills
    - Present skill recommendations to user during interview phase
    - WARN user that installing skills may require Claude restart
    - If skill is needed mid-implementation: search, recommend, but ASK before installing (restart required)

  * Skill Installation Flow:
    - Early discovery (Phase 1-2): Install skills proactively, warn about restart
    - Late discovery (Phase 7+): Ask user if they want to install (will interrupt flow)
    - Document all installed skills in knowledge base
    - Verify skill registration after restart

  * Research Agent Responsibilities:
    - Use WebSearch tool for implementation research
    - Use WebFetch to read documentation pages
    - Evaluate multiple sources before recommending approaches
    - Prefer official documentation over blog posts
    - Store research findings with source URLs

Documenation
------------
Projects should be delivered with complete and useful documentation, both user documentation adn developer documentation, as well as evidence of how the process worked.

Claude Quotas
-------------
It is VITAL that the plugin loop detect when claude is at or near a usage limit - .  Bundle this!  When the usage level hits the threshold of 85% for EITHER the current session, OR the weekly quoate, all agents should pause new requests until the quota is reset - check it every 10 minbutes in that case.  Check it before each agent interaction - store the current state in a file everyone can read, and cache it.  one way you could potentially do this is run "claude /usage", and then after it displays the usage, sent it escape, followed by /quit, to exit.  you should make a small python script that does this!!!

Note that it should NOT stop being autonomous at this time, just PAUSE.

Resume Command Behavior (REQUIRED)
----------------------------------
The `/beyond-ralph-resume` command MUST NOT blindly trust the state file. It MUST:

  * Always re-read and validate the SPEC.md against the stored hash
  * If spec has changed:
    - Identify NEW requirements added to the spec
    - Identify REMOVED requirements no longer in spec
    - Identify MODIFIED requirements that may need re-validation
    - Update the project plan accordingly
    - Schedule new tasks for new requirements
    - Mark affected modules for re-validation

  * Validate the project plan against the spec:
    - Every MUST/REQUIRED in spec has a corresponding task
    - All claimed completions are actually implemented
    - Tests actually exist and pass for "tested" items

  * The state file records progress, but the SPEC is the source of truth
  * A project is only truly "complete" when ALL current spec requirements are met
  * Spec changes automatically un-complete the project until addressed

Project Installation (REQUIRED)
-------------------------------
Beyond Ralph MUST include a comprehensive installer that sets up projects for success:

  * `beyond-ralph install <project-path>` - Full development environment setup

  * The installer MUST install:
    - Beyond Ralph commands (/beyond-ralph, /beyond-ralph-resume, /beyond-ralph-status)
    - Stop hooks for autonomous operation
    - SuperClaude commands (no API keys required):
      * /sc:analyze - Code analysis
      * /sc:research - Deep web research
      * /sc:troubleshoot - Debugging assistance
      * /sc:test - Testing workflows
      * /sc:improve - Code improvement
      * /sc:implement - Implementation guidance
      * /sc:design - Architecture design
      * /sc:explain - Code explanations
      * /sc:cleanup - Dead code removal
      * /sc:git - Git operations
      * /sc:build - Build automation
      * /sc:document - Documentation generation
      * /sc:estimate - Effort estimation
      * /sc:task - Task management
      * /sc:workflow - Workflow generation
    - Additional useful commands:
      * /clarify - Requirement clarification
      * /bugs - Bug hunting
      * /audit - Code audit
      * /unit-tests - Test generation
      * /refactor - Refactoring guidance
      * /library-docs - Library documentation lookup
    - Development skills:
      * confidence-check - Pre-implementation validation
      * task-classifier - Complexity routing
      * context7-usage - Documentation lookup
      * orchestrator - Workflow orchestration
      * compact - Context management
    - MCP server configurations (no API keys required, default):
      * context7 - Library documentation lookup
      * sequential-thinking - Step-by-step reasoning
      * filesystem - File operations with safety controls
      * memory - Persistent memory across sessions
      * git - Git repository operations
      * fetch - Web content fetching
      * time - Time/timezone utilities
      * playwright - Browser automation (Microsoft official)
      * sqlite - SQLite database operations
      * mcp-inspector - MCP server debugging
      * duckduckgo - Privacy-focused web search (REQUIRED for research without API keys)
      * arxiv - Academic paper search and retrieval
      * wikipedia - Wikipedia article search and retrieval

    - MCP servers with free tiers (require API keys, --allow-free-tier-with-key):
      * brave-search - Web search (free: 2000 queries/month)
      * tavily - AI-optimized search (free: 1000 queries/month)
      * github - GitHub API integration (uses personal access token)
      * sentry - Error tracking and debugging

  * Installation modes:
    - Full (default): All commands, skills, and no-API-key MCP configurations
    - With free tier: --allow-free-tier-with-key adds servers that need API keys but have free tiers
    - Minimal (--minimal): Just Beyond Ralph basics
    - Custom: --no-superclaude, --no-mcp flags for selective installation

  * The installer should copy from the user's global ~/.claude/ directory where these skills
    are already installed, allowing Beyond Ralph to leverage existing tooling.

  * Optional flags:
    - --install-mcp-packages: Actually install MCP packages via npm
    - --allow-free-tier-with-key: Include MCP servers with free tiers that need API keys

Implementation Details
----------------------
To implement this, you'll obviously need to use claude plkugins and stop hooks - the goal is for this flow to run within claude code itself, not as an external bash loop (hence all of the agents and such).  But you should also make claude skills adn agents to drive the actual flow - for example, I suspect the agent managemnet would be a skill.  use your best judgement while working this out!!!

Thank you for your time on this!!!  Hopefully we can come up with a fgully integrated way to do autonomous multi-agent development in claude code - i can tell you taht this model works great at my employer, who have their own system for it, but which uses regular code LLMs behind it, so I know we can do this!  we just have to do the implenentation!
