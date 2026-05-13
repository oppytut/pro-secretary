# 🎯 PROJECT RULES - AI Personal Secretary Stack

**Enforcement Level:** MANDATORY  
**Applies To:** All agents working on this project  
**Last Updated:** 2026-05-08

---

## 🔄 TASK.md UPDATE PROTOCOL (MANDATORY)

### Rule: Update TASK.md After EVERY Completed Task

**WHEN:** Immediately after completing ANY work unit (bug fix, feature, refactor, documentation, etc.)

**WHAT TO UPDATE:**

1. **CURRENT WORK Section**
   - Mark completed items with ✅
   - Move to "Recently Completed" with timestamp
   - Update progress on in-progress items
   - Add new blockers if discovered

2. **NEXT STEPS Section**
   - Remove completed items
   - Re-prioritize remaining tasks
   - Add newly discovered tasks

3. **KNOWN ISSUES Section**
   - Add any gotchas discovered during work
   - Document workarounds applied

4. **Last Updated Timestamp**
   - Update to current date

5. **Communication Notes**
   - Add brief summary for next agent
   - Document any decisions made
   - Note any deviations from plan

### Enforcement Pattern

```typescript
// WRONG: Complete work and end session
task_complete() → end_session()

// CORRECT: Complete work → update TASK.md → end session
task_complete() → update_task_md() → end_session()
```

### Update Template

When updating TASK.md, use this format:

```markdown
### Recently Completed
- ✅ [YYYY-MM-DD HH:MM] Task description
  - What was done
  - Files changed: path/to/file1, path/to/file2
  - Notes: any important context

### Communication Notes
> [YYYY-MM-DD HH:MM] Brief summary of what was accomplished.
> Next agent should: [specific guidance]
```

---

## 📋 WORKFLOW ENFORCEMENT

### Standard Task Completion Flow

```
1. Receive task
2. Read TASK.md for context
3. Execute work
4. Verify/test changes
5. Update TASK.md (MANDATORY)
6. Commit changes (if applicable)
7. Report completion to user
```

**BLOCKING RULE:** Step 5 (Update TASK.md) is NOT optional. Task is NOT complete until TASK.md is updated.

---

## 🚫 ANTI-PATTERNS (FORBIDDEN)

### ❌ Completing Work Without Update
```
# WRONG
agent: "Done! I've implemented the Docker Compose file."
# (TASK.md not updated - next agent has no visibility)
```

### ✅ Correct Pattern
```
# CORRECT
agent: "Done! I've implemented the Docker Compose file."
# (Updates TASK.md with completion, files changed, next steps)
agent: "TASK.md updated with completion status."
```

---

## 🎯 SPECIFIC UPDATE REQUIREMENTS

### For Code Changes
- List all files created/modified
- Note any new dependencies added
- Document configuration changes
- Update testing checklist if applicable

### For Bug Fixes
- Document the bug that was fixed
- Explain root cause
- Note any related issues discovered
- Update KNOWN ISSUES if pattern found

### For Infrastructure Changes
- Document new services/containers
- Note port changes
- Update environment variables needed
- Add to testing checklist

### For Documentation
- Note what was documented
- Update reference links if added
- Mark documentation tasks complete

---

## 🔍 VERIFICATION CHECKLIST

Before ending session, verify:

- [ ] TASK.md "Last Updated" timestamp is current
- [ ] Completed work moved to "Recently Completed"
- [ ] "Communication Notes" has entry for next agent
- [ ] "NEXT STEPS" reflects current state
- [ ] Any new blockers documented
- [ ] Files changed are listed

---

## 🤖 AGENT SELF-CHECK

Before reporting "task complete" to user, ask yourself:

1. ✅ Did I update TASK.md?
2. ✅ Will the next agent understand what I did?
3. ✅ Are there any gotchas I should document?
4. ✅ Did I update the priority of remaining tasks?

**If ANY answer is NO → Update TASK.md before completing.**

---

## 📝 EXAMPLE UPDATE

### Before Work
```markdown
### Active Tasks
- [ ] Create docker-compose.yml
- [ ] Create .env.example
```

### After Work (MANDATORY UPDATE)
```markdown
### Active Tasks
- [ ] Create .env.example

### Recently Completed
- ✅ [2026-05-08 14:30] Create docker-compose.yml
  - Created complete Docker Compose configuration
  - Files: docker-compose.yml
  - Services: n8n, langgraph-agent, calcom, telegram-bot, caddy
  - Tested: All containers start successfully
  - Notes: External PostgreSQL (Supabase/Neon), external Qdrant Cloud, external Cloudflare R2

### Communication Notes
> [2026-05-08 14:30] Docker Compose infrastructure complete. All 5 local services configured with proper networking and volumes. External services (PostgreSQL, Qdrant, R2) referenced via env vars. Next: Create .env.example with all required variables (see docker-compose.yml for reference).
```

---

## 🎓 WHY THIS MATTERS

### Without TASK.md Updates
- ❌ Next agent starts blind
- ❌ Work gets duplicated
- ❌ Decisions get lost
- ❌ User has no visibility
- ❌ Context fragmentation

### With TASK.md Updates
- ✅ Seamless handoffs
- ✅ Full visibility
- ✅ Decision history preserved
- ✅ No duplicate work
- ✅ Clear progress tracking

---

## 🔧 AUTOMATION HOOK

This rule is enforced by:
1. **Agent system prompt** - Includes TASK.md update requirement
2. **This RULES.md file** - Read at session start
3. **Manual verification** - User can check TASK.md for updates

**Future Enhancement:** Git pre-commit hook to verify TASK.md was updated in the same commit as code changes.

---

## 📞 ESCALATION

If you're unsure what to update in TASK.md:
1. At minimum: Update "Last Updated" + add entry to "Recently Completed"
2. Add note to "Communication Notes" explaining uncertainty
3. Ask user for guidance on what to track

**Better to over-document than under-document.**

---

## 🎯 COMPLIANCE

**This is a HARD RULE, not a guideline.**

Completing work without updating TASK.md is equivalent to:
- Committing code without tests
- Deploying without documentation
- Merging without review

**Non-negotiable. No exceptions.**
