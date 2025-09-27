
# Implementation Plan: Replace PyHomeBroker with PyRofex

**Branch**: `001-replace-pyhomebroker-dependency` | **Date**: 2025-09-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-replace-pyhomebroker-dependency/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Replace pyhomebroker dependency with pyRofex for market data access using COCOS broker. Maintain Excel integration via xlwings, implement websocket-based real-time updates with proper error handling, symbol transformation, and data validation. Focus on simplicity and operational reliability without formal testing frameworks per constitution principles.

## Technical Context
**Language/Version**: Python 3.x  
**Primary Dependencies**: pyRofex, xlwings, pandas (replacing pyhomebroker)  
**Storage**: Excel files (.xlsb format) via xlwings integration  
**Testing**: N/A - Per constitution Principle V: No Testing Overhead for utility scripts  
**Target Platform**: Windows (Excel integration requirement)
**Project Type**: single - Simple utility script with helper module  
**Performance Goals**: 2-second update frequency, <30s market data refresh, non-blocking Excel updates  
**Constraints**: Must maintain Excel file compatibility, preserve existing workbook structure, COCOS broker API endpoints  
**Scale/Scope**: Single user utility, ~500 financial instruments, real-time market data streaming

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Simplicity First ✅
- Replacing pyhomebroker with pyRofex maintains minimal dependency approach
- Using vanilla Python with essential libraries only (pyRofex, xlwings, pandas)
- No over-engineering, clear readable code preferred

### Principle II: Excel Live Integration ✅
- Maintains xlwings integration for live Excel updates
- Preserves .xlsb format compatibility
- Existing Excel structure and formatting preserved

### Principle III: Real-time Data Updates ✅
- Websocket integration provides continuous market data
- Non-blocking updates via proper error handling
- Exponential backoff reconnection strategy defined

### Principle IV: Configuration Transparency ✅
- Symbol transformation rules clearly defined ("MERV - XMEV - " prefix, "spot" → "CI")
- Tickers sheet configuration approach maintained
- COCOS broker endpoint configuration explicitly specified

### Principle V: No Testing Overhead ✅
- No unit tests or TDD practices required
- Focus on operational reliability through error handling
- Logging and error messages for troubleshooting

**GATE STATUS**: PASS - All constitutional principles satisfied

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Single project structure (existing codebase)
main_HM.py              # Main execution script - to be updated
Options_Helper_HM.py    # Helper module - to be updated  
EPGB OC-DI - Python.xlsb  # Excel workbook (unchanged)
```

**Structure Decision**: Single project structure maintained. Existing Python scripts will be modified to replace pyhomebroker with pyRofex integration while preserving Excel workbook structure and helper module organization.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks based on constitutional principles (no formal testing required)
- Focus on modifying existing files (main_HM.py, Options_Helper_HM.py)
- Each major function change → implementation task
- Symbol transformation logic → separate task
- Error handling implementation → separate task  
- Excel integration verification → validation task

**Ordering Strategy**:
- Constitutional order: Operational reliability over test-driven development
- Dependency order: Environment setup → Authentication → WebSocket → Data processing → Excel integration
- Mark [P] for parallel execution (independent file modifications)
- Sequential for dependent operations (auth before connection, connection before subscription)

**Estimated Output**: 15-20 numbered, ordered tasks in tasks.md focusing on:
1. Environment and dependency setup
2. pyRofex initialization and authentication
3. Symbol transformation implementation
4. WebSocket connection and handlers
5. Market data processing and validation
6. Excel integration updates
7. Error handling implementation
8. Manual validation and testing

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (N/A - no deviations)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
