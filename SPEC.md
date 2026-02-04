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

    * If the app needs to interact with _any other resources_, those resources MUST be provided by the user up front!
       * The first thing claude should do with this, is check that _everyhting_ it needs is available - this should ne a part of the inteview process described above!!!
       * The user can opt to allow claude to autonomously install thigns on the system - if the user agrees to this, the agents should fetch and preapre their own deependencies!!!

Documenation
------------
Projects should be delivered with complete and useful documentation, both user documentation adn developer documentation, as well as evidence of how the process worked.

Claude Quotas
-------------
It is VITAL that the plugin loop detect when claude is at or near a usage limit - .  Bundle this!  When the usage level hits the threshold of 85% for EITHER the current session, OR the weekly quoate, all agents should pause new requests until the quota is reset - check it every 10 minbutes in that case.  Check it before each agent interaction - store the current state in a file everyone can read, and cache it.  one way you could potentially do this is run "claude /usage", and then after it displays the usage, sent it escape, followed by /quit, to exit.  you should make a small python script that does this!!!

BNote that it should NOT stop being autonomous at this time, just PAUSE.

Implementation Details
----------------------
To implement this, you'll obviously need to use claude plkugins and stop hooks - the goal is for this flow to run within claude code itself, not as an external bash loop (hence all of the agents and such).  But you should also make claude skills adn agents to drive the actual flow - for example, I suspect the agent managemnet would be a skill.  use your best judgement while working this out!!!

Thank you for your time on this!!!  Hopefully we can come up with a fgully integrated way to do autonomous multi-agent development in claude code - i can tell you taht this model works great at my employer, who have their own system for it, but which uses regular code LLMs behind it, so I know we can do this!  we just have to do the implenentation!
